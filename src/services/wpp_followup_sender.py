"""
WPP Follow-up Sender - Envía un WhatsApp de seguimiento tras enviar el email.

Después de que el Hunter Bot envía un email exitosamente, este servicio envía
un mensaje de WhatsApp via Twilio Content API informando al contacto que
acaba de recibir un correo.

Usa 5 templates diferentes aprobados por Meta en rotación para evitar detección
de spam por parte de WhatsApp/Meta.

Variables de entorno requeridas:
    TWILIO_ACCOUNT_SID  (fallback: ACCOUNT_SID)
    TWILIO_API_KEY_SID  (fallback: API_KEY_SID)
    TWILIO_API_KEY_SECRET (fallback: API_KEY_SECRET)
    HUNTER_FROM_WPP_NUMBER  (default: whatsapp:+5491125303794)
    WPP_FOLLOWUP_SID_0 .. WPP_FOLLOWUP_SID_4  — Content SIDs aprobados en Twilio

Templates sugeridos (crear en Twilio Content Templates y pegar los SIDs):
    0: "¡Hola {{1}}! Les acabo de enviar un correo con información sobre cómo
        potenciar su presencia digital. Cualquier consulta, estoy disponible
        por aquí. ¡Saludos!"
    1: "Hola {{1}}, recién les enviamos un email con una propuesta para su
        negocio. Si prefieren coordinar por WhatsApp, ¡estamos a disposición!"
    2: "¡Buenas {{1}}! Les mandé un correo hace un momento detallando cómo
        podemos ayudar a su negocio online. Por si no llegó, puede estar en
        spam. ¡Cualquier duda, estamos por acá!"
    3: "Hola {{1}}! Les enviamos un mail con detalles sobre nuestros servicios.
        Si tienen un momento para charlar, ¡con gusto les cuento más por este
        medio también!"
    4: "¡Qué tal {{1}}! Justo les dejé un email con información relevante para
        su negocio. Si prefieren que les cuente directamente por aquí,
        ¡avisá y lo hacemos!"
"""

import asyncio
import base64
import json
import os
import random
import re
from typing import Optional

import httpx
from dotenv import load_dotenv

from src.utils.logger import log

load_dotenv()

TWILIO_MESSAGES_URL = (
    "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
)
FOLLOWUP_TEMPLATE_SLOTS = 5


class WppFollowupSender:
    """
    Envía un WhatsApp de seguimiento justo después de que se envía un email.

    Si alguna credencial de Twilio falta o no hay SIDs configurados,
    el servicio queda deshabilitado y send() es un no-op silencioso,
    sin lanzar excepciones, para no interrumpir el flujo principal.
    """

    def __init__(self) -> None:
        self._account_sid = (
            os.getenv("TWILIO_ACCOUNT_SID") or os.getenv("ACCOUNT_SID") or ""
        ).strip()
        self._api_key_sid = (
            os.getenv("TWILIO_API_KEY_SID") or os.getenv("API_KEY_SID") or ""
        ).strip()
        self._api_key_secret = (
            os.getenv("TWILIO_API_KEY_SECRET") or os.getenv("API_KEY_SECRET") or ""
        ).strip()
        self._from_number = (
            os.getenv("HUNTER_FROM_WPP_NUMBER", "whatsapp:+5491125303794")
        ).strip()

        # Cargar hasta FOLLOWUP_TEMPLATE_SLOTS SIDs configurados
        self._template_sids: list[str] = []
        for i in range(FOLLOWUP_TEMPLATE_SLOTS):
            sid = (os.getenv(f"WPP_FOLLOWUP_SID_{i}") or "").strip()
            if sid:
                self._template_sids.append(sid)

        self._enabled = bool(
            self._account_sid
            and self._api_key_sid
            and self._api_key_secret
            and self._template_sids
        )

        if not self._enabled:
            missing = []
            if not self._account_sid:
                missing.append("TWILIO_ACCOUNT_SID")
            if not self._api_key_sid:
                missing.append("TWILIO_API_KEY_SID")
            if not self._api_key_secret:
                missing.append("TWILIO_API_KEY_SECRET")
            if not self._template_sids:
                missing.append("WPP_FOLLOWUP_SID_0 (al menos 1 SID)")
            log.warning(
                f"WppFollowupSender deshabilitado — faltan: {', '.join(missing)}. "
                "Los follow-ups de WPP serán omitidos hasta que se configuren."
            )
        else:
            log.success(
                f"WppFollowupSender listo con {len(self._template_sids)} "
                f"template(s) de seguimiento."
            )

        self._http_client = httpx.AsyncClient(timeout=15)
        # Empezar en un índice aleatorio para distribuir los templates
        self._current_index = (
            random.randint(0, len(self._template_sids) - 1)
            if self._template_sids
            else 0
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    async def send(self, wpp_number: str, company_name: str) -> bool:
        """
        Envía el mensaje de seguimiento de WhatsApp.

        Args:
            wpp_number: Número de WPP del destinatario (cualquier formato aceptado).
            company_name: Nombre de la empresa / lead para personalizar el template.

        Returns:
            True si el mensaje fue enviado exitosamente, False en cualquier otro caso.
        """
        if not self._enabled:
            return False

        to_number = self._normalize_phone(wpp_number)
        if not to_number:
            log.warning(
                f"WPP follow-up: número inválido '{wpp_number}', omitiendo."
            )
            return False

        content_sid = self._next_template_sid()
        content_variables = json.dumps({"1": company_name or "su empresa"})

        url = TWILIO_MESSAGES_URL.format(account_sid=self._account_sid)
        payload = {
            "From": self._from_number,
            "To": to_number,
            "ContentSid": content_sid,
            "ContentVariables": content_variables,
        }

        for attempt in range(3):
            try:
                response = await self._http_client.post(
                    url,
                    data=payload,
                    headers={"Authorization": self._build_auth_header()},
                )

                if response.status_code == 201:
                    twilio_sid = response.json().get("sid", "")
                    log.success(
                        f"WPP follow-up enviado → {to_number} "
                        f"(SID: {twilio_sid}, template idx: {(self._current_index - 1) % len(self._template_sids)})"
                    )
                    return True

                # Errores reintentables
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    wait = 2 ** (attempt + 1)
                    log.warning(
                        f"WPP follow-up: Twilio {response.status_code}, "
                        f"reintentando en {wait}s (intento {attempt + 1}/3)"
                    )
                    await asyncio.sleep(wait)
                    continue

                error_body = response.text[:200]
                log.error(
                    f"WPP follow-up fallido (HTTP {response.status_code}): {error_body}"
                )
                return False

            except (httpx.TransportError, httpx.TimeoutException) as exc:
                if attempt < 2:
                    wait = 2 ** (attempt + 1)
                    log.warning(
                        f"WPP follow-up: error de red, reintentando en {wait}s — {exc}"
                    )
                    await asyncio.sleep(wait)
                else:
                    log.error(f"WPP follow-up: error de red definitivo — {exc}")
                    return False

        return False

    async def close(self) -> None:
        """Cierra el cliente HTTP y libera conexiones."""
        await self._http_client.aclose()

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _next_template_sid(self) -> str:
        """Rota entre los SIDs disponibles de forma circular."""
        sid = self._template_sids[self._current_index % len(self._template_sids)]
        self._current_index = (self._current_index + 1) % len(self._template_sids)
        return sid

    def _build_auth_header(self) -> str:
        """Construye el header de autenticación Basic para Twilio."""
        credentials = f"{self._api_key_sid}:{self._api_key_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @staticmethod
    def _normalize_phone(phone: str) -> Optional[str]:
        """
        Normaliza un número de teléfono al formato de Twilio WhatsApp:
        'whatsapp:+549XXXXXXXXXX' (para Argentina) o 'whatsapp:+XXXXXXXXXXX'.

        Maneja:
        - Links wa.me/... y api.whatsapp.com/send?phone=...
        - Ya en formato 'whatsapp:+...'
        - Números argentinos: 549XXXXXXXXXX, 54XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX
        - Números internacionales con/sin '+'

        Devuelve None si el número no puede ser normalizado.
        """
        if not phone:
            return None

        phone = phone.strip()

        # wa.me/5491112345678 o wa.me/+5491112345678
        wa_me = re.search(r'wa\.me/\+?(\d{7,15})', phone)
        if wa_me:
            return f"whatsapp:+{wa_me.group(1)}"

        # api.whatsapp.com/send?phone=5491112345678
        api_wpp = re.search(r'phone=\+?(\d{7,15})', phone, re.IGNORECASE)
        if api_wpp:
            return f"whatsapp:+{api_wpp.group(1)}"

        # Ya en formato Twilio: whatsapp:+NUMBER
        if phone.lower().startswith('whatsapp:'):
            inner = phone[9:].strip()
            digits = re.sub(r'\D', '', inner)
            if 7 <= len(digits) <= 15:
                return f"whatsapp:+{digits}"
            return None

        # Extraer solo dígitos
        digits = re.sub(r'\D', '', phone)
        if not digits:
            return None

        # Argentina: 549 + 10 dígitos = 13 dígitos totales
        if len(digits) == 13 and digits.startswith('549'):
            return f"whatsapp:+{digits}"

        # Argentina: 54 + 10 dígitos (sin el 9 intermedio) = 12 dígitos
        if len(digits) == 12 and digits.startswith('54') and not digits.startswith('549'):
            return f"whatsapp:+549{digits[2:]}"

        # Formato local argentino: 0 + 10 dígitos = 11 dígitos
        if len(digits) == 11 and digits.startswith('0'):
            return f"whatsapp:+549{digits[1:]}"

        # 10 dígitos solos: asumir Argentina
        if len(digits) == 10:
            return f"whatsapp:+549{digits}"

        # Internacional: 7–15 dígitos con cualquier prefijo de país
        if 7 <= len(digits) <= 15:
            return f"whatsapp:+{digits}"

        return None
