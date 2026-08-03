"""Budget period date helpers."""

from __future__ import annotations

from datetime import date, timedelta


def resolve_period_end(period: str, start_date: date) -> date:
    """Compute a period's end date from its start date."""
    if period == "weekly":
        return start_date + timedelta(days=6)
    if period == "biweekly":
        return start_date + timedelta(days=13)
    if period == "monthly":
        if start_date.month == 12:
            return start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        return start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    if period == "quarterly":
        quarter_month = ((start_date.month - 1) // 3 + 1) * 3
        if quarter_month >= 12:
            return start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        return start_date.replace(month=quarter_month + 1, day=1) - timedelta(days=1)
    return start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)


def next_period_dates(period: str, end_date: date) -> tuple[date, date]:
    """Return (start, end) dates of the period following the one that ends on ``end_date``."""
    next_start = end_date + timedelta(days=1)
    return next_start, resolve_period_end(period, next_start)
