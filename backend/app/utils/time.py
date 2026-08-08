"""Timezone helpers — centralize "today" resolution for user-local dates."""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "America/Santo_Domingo"


def today_in(tz: str = DEFAULT_TIMEZONE) -> date:
    """Return the current date in the given IANA timezone (default DR)."""
    return datetime.now(ZoneInfo(tz)).date()


def utc_now() -> datetime:
    """Return the current UTC-aware datetime."""
    return datetime.now(UTC)
