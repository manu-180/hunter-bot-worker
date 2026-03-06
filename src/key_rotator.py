"""
SerpAPI Key Rotator — rotación automática de múltiples API keys.

Lee keys desde SERPAPI_KEYS (comma-separated) con fallback a SERPAPI_KEY.
Rota automáticamente cuando una key se queda sin créditos o recibe rate-limit.

Env vars:
    SERPAPI_KEYS=key1,key2,key3     Múltiples keys separadas por coma
    SERPAPI_KEY=key1                 Fallback: key única (backwards compatible)
"""

import asyncio
import json
import logging
import os
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional

log = logging.getLogger("domain_hunter")

# Verificar créditos cada 180s (antes 300s): detecta keys al límite más rápido.
# El endpoint /account.json es gratuito y no consume créditos de búsqueda.
CREDIT_CHECK_INTERVAL = 180
# Buffer de 15 créditos antes de rotar (antes 5): evita los errores "run out of searches"
# que ocurrían cuando la key llegaba a 0 antes de que el rotador actuara.
MIN_CREDITS_THRESHOLD = 15


@dataclass
class _KeyState:
    key: str
    credits_left: Optional[int] = None
    last_credit_check: float = 0.0
    searches_done: int = 0
    errors: int = 0
    exhausted: bool = False
    rate_limited_until: float = 0.0

    @property
    def masked(self) -> str:
        if len(self.key) <= 8:
            return "***"
        return f"{self.key[:4]}...{self.key[-4:]}"


class SerpApiKeyRotator:
    """Rotador thread-safe de API keys de SerpAPI con auto-failover."""

    def __init__(self) -> None:
        raw_keys = os.getenv("SERPAPI_KEYS", "").strip()
        single_key = os.getenv("SERPAPI_KEY", "").strip()

        keys: List[str] = []
        if raw_keys:
            keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        if not keys and single_key:
            keys = [single_key]

        if not keys:
            raise ValueError(
                "No hay SerpAPI keys configuradas. "
                "Seteá SERPAPI_KEYS=key1,key2,... o SERPAPI_KEY=key en las variables de entorno."
            )

        seen: set = set()
        unique: List[str] = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                unique.append(k)

        self._states: List[_KeyState] = [_KeyState(key=k) for k in unique]
        self._current_idx: int = 0
        self._lock = asyncio.Lock()

        log.info(
            f"🔑 KeyRotator inicializado con {len(self._states)} key(s): "
            + ", ".join(s.masked for s in self._states)
        )

    @property
    def total_keys(self) -> int:
        return len(self._states)

    @property
    def current_key(self) -> str:
        return self._states[self._current_idx].key

    @property
    def current_masked(self) -> str:
        return self._states[self._current_idx].masked

    async def get_key(self) -> str:
        """Devuelve la key activa. Rota si la actual está agotada o rate-limited."""
        async with self._lock:
            state = self._states[self._current_idx]
            now = time.time()

            if state.exhausted or now < state.rate_limited_until:
                rotated = self._rotate_to_next()
                if rotated:
                    return self._states[self._current_idx].key
                if state.exhausted:
                    log.warning("⚠️ Todas las keys agotadas, forzando re-check de créditos")
                    for s in self._states:
                        s.last_credit_check = 0.0
                        s.exhausted = False

            return self._states[self._current_idx].key

    async def report_success(self) -> None:
        """Registra una búsqueda exitosa en la key actual."""
        async with self._lock:
            state = self._states[self._current_idx]
            state.searches_done += 1
            state.errors = 0
            if state.credits_left is not None:
                state.credits_left = max(0, state.credits_left - 1)
                if state.credits_left < MIN_CREDITS_THRESHOLD:
                    state.exhausted = True
                    log.warning(
                        f"⚠️ Key {state.masked} con solo {state.credits_left} créditos tras búsqueda. Rotando..."
                    )
                    self._rotate_to_next()

    async def report_error(self, error_msg: str = "") -> None:
        """Registra un error. Si parece rate-limit o key inválida, rota."""
        async with self._lock:
            state = self._states[self._current_idx]
            state.errors += 1
            lower = error_msg.lower()

            if "rate" in lower or "limit" in lower or "429" in lower or "too many" in lower:
                state.rate_limited_until = time.time() + 120
                log.warning(
                    f"🔄 Key {state.masked} rate-limited, cooldown 2min. Rotando..."
                )
                self._rotate_to_next()
            elif "invalid" in lower or "unauthorized" in lower or "403" in lower:
                state.exhausted = True
                log.warning(f"🔄 Key {state.masked} inválida/expirada. Rotando...")
                self._rotate_to_next()
            elif "run out" in lower or "out of searches" in lower:
                state.exhausted = True
                log.warning(f"🔄 Key {state.masked} sin créditos (run out of searches). Rotando...")
                self._rotate_to_next()
            elif state.errors >= 5:
                log.warning(
                    f"🔄 Key {state.masked} con {state.errors} errores consecutivos. Rotando..."
                )
                self._rotate_to_next()

    async def check_credits(self) -> Optional[int]:
        """Verifica créditos de la key actual (gratis, no gasta créditos).
        
        Returns: créditos restantes o None si falla.
        Auto-rota si la key no tiene créditos.
        """
        async with self._lock:
            state = self._states[self._current_idx]
            now = time.time()
            if now - state.last_credit_check < CREDIT_CHECK_INTERVAL:
                return state.credits_left
            key_to_check = state.key
            state_ref = state

        try:
            url = f"https://serpapi.com/account.json?api_key={key_to_check}"
            req = urllib.request.Request(url)
            data = await asyncio.to_thread(
                lambda: urllib.request.urlopen(req, timeout=10).read()
            )
            info = json.loads(data.decode())
            left = info.get("total_searches_left", 0)
            plan = info.get("plan_name", "N/A")
            used = info.get("this_month_usage", 0)

            async with self._lock:
                state_ref.credits_left = left
                state_ref.last_credit_check = time.time()

                log.info(
                    f"💰 Key {state_ref.masked}: {left} créditos restantes | "
                    f"Plan: {plan} | Usadas este mes: {used}"
                )

                if left < MIN_CREDITS_THRESHOLD:
                    state_ref.exhausted = True
                    log.warning(
                        f"⚠️ Key {state_ref.masked} con solo {left} créditos. Rotando..."
                    )
                    self._rotate_to_next()

            return left
        except Exception as e:
            log.error(f"❌ Error verificando créditos de {state_ref.masked}: {e}")
            return state_ref.credits_left

    async def check_all_credits(self) -> Dict[str, int]:
        """Verifica créditos de TODAS las keys. Retorna {masked_key: credits}."""
        result: Dict[str, int] = {}
        for state in self._states:
            try:
                url = f"https://serpapi.com/account.json?api_key={state.key}"
                req = urllib.request.Request(url)
                data = await asyncio.to_thread(
                    lambda: urllib.request.urlopen(req, timeout=10).read()
                )
                info = json.loads(data.decode())
                left = info.get("total_searches_left", 0)
                state.credits_left = left
                state.last_credit_check = time.time()
                state.exhausted = left < MIN_CREDITS_THRESHOLD
                result[state.masked] = left
            except Exception as e:
                log.error(f"❌ Error verificando créditos de {state.masked}: {e}")
                result[state.masked] = state.credits_left or -1
        total = sum(v for v in result.values() if v >= 0)
        log.info(
            f"🔑 Resumen de keys: {total} créditos totales | "
            + " | ".join(f"{k}: {v}" for k, v in result.items())
        )
        return result

    def get_stats(self) -> str:
        """Devuelve un string con estadísticas de todas las keys."""
        lines = [f"🔑 KeyRotator — {len(self._states)} keys:"]
        for i, s in enumerate(self._states):
            marker = "→ " if i == self._current_idx else "  "
            status = "AGOTADA" if s.exhausted else "OK"
            if time.time() < s.rate_limited_until:
                status = "RATE-LIMITED"
            credits_str = str(s.credits_left) if s.credits_left is not None else "?"
            lines.append(
                f"{marker}{s.masked} | {status} | "
                f"créditos: {credits_str} | búsquedas: {s.searches_done}"
            )
        return "\n".join(lines)

    def _rotate_to_next(self) -> bool:
        """Rota a la siguiente key disponible. Retorna True si encontró una."""
        now = time.time()
        original = self._current_idx
        for _ in range(len(self._states)):
            self._current_idx = (self._current_idx + 1) % len(self._states)
            candidate = self._states[self._current_idx]
            if not candidate.exhausted and now >= candidate.rate_limited_until:
                log.info(f"🔄 Rotando a key {candidate.masked}")
                return True
        self._current_idx = original
        log.warning("⚠️ No hay keys disponibles para rotar, manteniendo la actual")
        return False
