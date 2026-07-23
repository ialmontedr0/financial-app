"""Calendar handler unit tests."""

import pytest


class TestCalendarHandler:
    def test_recurring_transactions_to_ics(self):
        from app.integrations.calendar_handler import recurring_transactions_to_ics

        txs = [
            {
                "description": "Netflix",
                "amount": 15.99,
                "type": "expense",
                "frequency": "monthly",
                "next_execution_date": "2024-02-01",
            },
        ]
        ics = recurring_transactions_to_ics(txs)
        assert "BEGIN:VCALENDAR" in ics
        assert "Netflix" in ics
        assert "RRULE:FREQ=MONTHLY" in ics

    def test_goals_to_ics(self):
        from app.integrations.calendar_handler import goals_to_ics

        goals = [
            {
                "name": "Car Fund",
                "target_amount": 20000,
                "current_amount": 5000,
                "target_date": "2025-06-01",
                "status": "active",
                "progress_pct": 25.0,
            },
        ]
        ics = goals_to_ics(goals)
        assert "BEGIN:VCALENDAR" in ics
        assert "Car Fund" in ics
        assert "VALARM" in ics

    def test_empty_recurring(self):
        from app.integrations.calendar_handler import recurring_transactions_to_ics

        ics = recurring_transactions_to_ics([])
        assert "BEGIN:VCALENDAR" in ics
