"""
Timezone utilities for HunterBot.

Centralizes all timezone conversion logic to avoid duplication
and handle DST correctly using zoneinfo.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
UTC = timezone.utc


def argentina_now() -> datetime:
    """Get the current datetime in Argentina timezone."""
    return datetime.now(ARGENTINA_TZ)


def utc_now() -> datetime:
    """Get the current datetime in UTC (timezone-aware)."""
    return datetime.now(UTC)


def argentina_hour() -> int:
    """Get the current hour in Argentina timezone."""
    return argentina_now().hour


def is_business_hours(start: int = 8, end: int = 18) -> bool:
    """
    Check if current time is within business hours (Argentina).

    Args:
        start: Business hours start (default 8 AM)
        end: Business hours end (default 6 PM)

    Returns:
        True if within business hours
    """
    hour = argentina_hour()
    return start <= hour < end


def format_argentina_time() -> str:
    """Get formatted Argentina time string (HH:MM)."""
    now = argentina_now()
    return f"{now.hour:02d}:{now.minute:02d}"


def format_utc_time() -> str:
    """Get formatted UTC time string (HH:MM)."""
    now = utc_now()
    return f"{now.hour:02d}:{now.minute:02d}"
