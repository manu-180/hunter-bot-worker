"""
Centralized configuration for HunterBot.

All hardcoded values and environment variable defaults in one place.
Override any value via environment variables with HUNTER_ prefix.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _str(key: str, default: str) -> str:
    return os.getenv(key, default).strip() or default


def _float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


class BotConfig:
    """Centralized bot configuration with env-var overrides."""

    # ── Business hours (Argentina time) ──────────────────────────────────
    BUSINESS_HOURS_START: int = _int("HUNTER_BUSINESS_HOURS_START", 8)
    BUSINESS_HOURS_END: int = _int("HUNTER_BUSINESS_HOURS_END", 18)

    # ── LeadSniper Worker ────────────────────────────────────────────────
    SCRAPE_BATCH_SIZE: int = _int("HUNTER_SCRAPE_BATCH_SIZE", 5)
    EMAIL_BATCH_SIZE: int = _int("HUNTER_EMAIL_BATCH_SIZE", 3)
    SCRAPE_TIMEOUT: int = _int("HUNTER_SCRAPE_TIMEOUT", 20)
    EMAIL_MIN_DELAY: int = _int("HUNTER_EMAIL_MIN_DELAY", 10)
    EMAIL_MAX_DELAY: int = _int("HUNTER_EMAIL_MAX_DELAY", 30)
    IDLE_SLEEP_SECONDS: int = _int("HUNTER_IDLE_SLEEP", 10)
    HEARTBEAT_INTERVAL: int = _int("HUNTER_HEARTBEAT_INTERVAL", 60)

    # ── Domain Hunter Worker ─────────────────────────────────────────────
    MIN_DELAY_BETWEEN_SEARCHES: int = _int("HUNTER_SEARCH_MIN_DELAY", 2)
    MAX_DELAY_BETWEEN_SEARCHES: int = _int("HUNTER_SEARCH_MAX_DELAY", 5)
    CHECK_USERS_INTERVAL: int = _int("HUNTER_CHECK_USERS_INTERVAL", 60)
    PAUSE_CHECK_INTERVAL: int = _int("HUNTER_PAUSE_CHECK_INTERVAL", 300)

    # ── Resilience ───────────────────────────────────────────────────────
    MAX_RETRY_ATTEMPTS: int = _int("HUNTER_MAX_RETRIES", 3)
    ERROR_BACKOFF_BASE: float = _float("HUNTER_ERROR_BACKOFF_BASE", 5)
    ERROR_BACKOFF_MAX: float = _float("HUNTER_ERROR_BACKOFF_MAX", 120)

    # ── Caches ───────────────────────────────────────────────────────────
    SESSION_CACHE_MAX_SIZE: int = _int("HUNTER_SESSION_CACHE_MAX", 10000)
    CONFIG_CACHE_TTL: int = _int("HUNTER_CONFIG_CACHE_TTL", 300)

    # ── SerpAPI ──────────────────────────────────────────────────────────
    SERPAPI_TIMEOUT: int = _int("HUNTER_SERPAPI_TIMEOUT", 30)

    # ── Credit Management ────────────────────────────────────────────────
    CREDIT_CHECK_INTERVAL: int = _int("HUNTER_CREDIT_CHECK_INTERVAL", 10)  # Check every N searches
    CREDIT_RESERVE_MIN: int = _int("HUNTER_CREDIT_RESERVE_MIN", 50)       # Pause if fewer left
    CREDIT_PAUSE_SECONDS: int = _int("HUNTER_CREDIT_PAUSE_SECONDS", 3600) # Pause duration
    DEFAULT_DAILY_CREDIT_LIMIT: int = _int("HUNTER_DAILY_CREDIT_LIMIT", 200)  # Per user

    # ── Parallel Processing ──────────────────────────────────────────────
    MAX_CONCURRENT_USERS: int = _int("HUNTER_MAX_CONCURRENT_USERS", 3)

    # ── Límite total de emails (warm-up dominio) ──────────────────────────
    # Para que Outlook/Gmail confíen en el dominio, limitar envíos al inicio.
    # Una vez enviados MAX_TOTAL_EMAILS_SENT, el bot deja de buscar dominios
    # y de enviar más emails hasta que se cambie o desactive el límite.
    MAX_TOTAL_EMAILS_SENT: int = _int("HUNTER_MAX_TOTAL_EMAILS_SENT", 20)

    # ── Modo de email (lanzamiento vs completo) ────────────────────────────
    # "launch" = formato simple sin links para ganar confianza (primera semana).
    # "full" = formato completo BotLode con CTA y branding.
    # Cuando tengas buena reputación, cambia a "full" o env: HUNTER_EMAIL_MODE=full
    EMAIL_MODE: str = _str("HUNTER_EMAIL_MODE", "launch")
    # Asunto para modo launch: aburrido, que parezca humano (evita filtros).
    LAUNCH_SUBJECT: str = _str("HUNTER_LAUNCH_SUBJECT", "Consulta sobre su sitio web")
