"""Calendar (.ics) export handler for recurring transactions and goals."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from icalendar import Calendar, Event


def _make_uid() -> str:
    return f"{uuid4()}@fip"


def recurring_transactions_to_ics(
    recurring_txs: list[dict[str, Any]],
    user_email: str = "",
) -> str:
    """Export recurring transactions as ICS calendar events."""
    cal = Calendar()
    cal.add("prodid", "-//FIP//Recurring Transactions//ES")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "FIP - Recurring Transactions")
    if user_email:
        cal.add("x-wr-caldesc", f"Recurring transactions for {user_email}")

    for tx in recurring_txs:
        event = Event()
        event.add("uid", _make_uid())
        event.add(
            "summary",
            f"{tx.get('type', '').upper()}: {tx.get('description', 'Transaction')}",
        )
        event.add(
            "description",
            (
                f"Amount: {tx.get('amount', 0)} {tx.get('currency', 'DOP')}\n"
                f"Type: {tx.get('type', '')}\n"
                f"Category: {tx.get('category', '')}\n"
                f"Account: {tx.get('account', '')}"
            ),
        )

        next_date_str = tx.get("next_execution_date", "")
        if next_date_str:
            try:
                next_date = datetime.fromisoformat(
                    next_date_str.replace("Z", "+00:00")
                ).date()
            except (ValueError, AttributeError):
                next_date = datetime.now(UTC).date()
        else:
            next_date = datetime.now(UTC).date()

        event.add("dtstart", next_date)
        event.add("dtend", next_date + timedelta(days=1))
        event.add("transp", "TRANSPARENT")

        frequency = tx.get("frequency", "monthly").lower()
        rrule_map = {
            "daily": {"freq": "DAILY"},
            "weekly": {"freq": "WEEKLY"},
            "biweekly": {"freq": "WEEKLY", "interval": 2},
            "monthly": {"freq": "MONTHLY"},
            "quarterly": {"freq": "MONTHLY", "interval": 3},
            "yearly": {"freq": "YEARLY"},
        }
        rrule = rrule_map.get(frequency, {"freq": "MONTHLY"})
        event.add("rrule", rrule)

        cal.add_component(event)

    return cal.to_ical().decode("utf-8")


def goals_to_ics(
    goals: list[dict[str, Any]],
    user_email: str = "",
) -> str:
    """Export financial goals as ICS calendar events (deadline reminders)."""
    from icalendar import Alarm

    cal = Calendar()
    cal.add("prodid", "-//FIP//Financial Goals//ES")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "FIP - Financial Goals")
    if user_email:
        cal.add("x-wr-caldesc", f"Financial goals for {user_email}")

    for goal in goals:
        target_date_str = goal.get("target_date", "")
        if not target_date_str:
            continue

        try:
            target_date = datetime.fromisoformat(
                target_date_str.replace("Z", "+00:00")
            ).date()
        except (ValueError, AttributeError):
            continue

        event = Event()
        event.add("uid", _make_uid())
        event.add("summary", f"GOAL DEADLINE: {goal.get('name', 'Financial Goal')}")
        event.add(
            "description",
            (
                f"Target: {goal.get('target_amount', 0)} {goal.get('currency', 'DOP')}\n"
                f"Current: {goal.get('current_amount', 0)}\n"
                f"Progress: {goal.get('progress_pct', 0):.1f}%\n"
                f"Status: {goal.get('status', 'active')}"
            ),
        )
        event.add("dtstart", target_date)
        event.add("dtend", target_date + timedelta(days=1))
        event.add("transp", "TRANSPARENT")

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add(
            "description",
            f"Goal '{goal.get('name', '')}' deadline in 7 days",
        )
        alarm.add("trigger", timedelta(days=-7))
        event.add_component(alarm)

        cal.add_component(event)

        if goal.get("status") == "active":
            from dateutil.relativedelta import relativedelta

            check_date = datetime.now(UTC).date()
            while check_date < target_date:
                check_event = Event()
                check_event.add("uid", _make_uid())
                check_event.add("summary", f"CHECK: {goal.get('name', '')} progress")
                check_event.add(
                    "description",
                    f"Monthly progress check for goal: {goal.get('name', '')}",
                )
                check_event.add("dtstart", check_date)
                check_event.add("dtend", check_date + timedelta(days=1))
                check_event.add("transp", "TRANSPARENT")
                cal.add_component(check_event)
                check_date += relativedelta(months=1)

    return cal.to_ical().decode("utf-8")
