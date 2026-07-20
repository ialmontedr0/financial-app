"""Tests for transaction value objects."""

import pytest
from datetime import date

from app.domain.transactions.value_objects import (
    AuditAction,
    RecurrenceFrequency,
    TransactionSource,
    TransactionStatus,
    TransactionType,
)


class TestTransactionType:
    def test_valid_types(self):
        for t in ["income", "expense", "transfer", "adjustment"]:
            assert TransactionType(t).value == t

    def test_case_insensitive(self):
        assert TransactionType("INCOME").value == "income"

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            TransactionType("invalid")

    def test_name(self):
        assert TransactionType("income").name == "Ingreso"

    def test_str(self):
        assert str(TransactionType("expense")) == "expense"


class TestTransactionStatus:
    def test_valid_statuses(self):
        for s in ["draft", "pending", "completed", "cancelled", "failed"]:
            assert TransactionStatus(s).value == s

    def test_invalid_status(self):
        with pytest.raises(ValueError):
            TransactionStatus("unknown")


class TestTransactionSource:
    def test_valid_sources(self):
        for s in ["manual", "import", "recurring", "api", "ocr"]:
            assert TransactionSource(s).value == s

    def test_invalid_source(self):
        with pytest.raises(ValueError):
            TransactionSource("hack")


class TestRecurrenceFrequency:
    def test_valid_frequencies(self):
        for f in ["daily", "weekly", "biweekly", "monthly", "quarterly", "yearly"]:
            assert RecurrenceFrequency(f).value == f

    def test_calculate_next_daily(self):
        freq = RecurrenceFrequency("daily")
        assert freq.calculate_next_date(date(2026, 1, 1)) == date(2026, 1, 2)

    def test_calculate_next_weekly(self):
        freq = RecurrenceFrequency("weekly")
        assert freq.calculate_next_date(date(2026, 1, 1)) == date(2026, 1, 8)

    def test_calculate_next_monthly(self):
        freq = RecurrenceFrequency("monthly")
        assert freq.calculate_next_date(date(2026, 1, 15)) == date(2026, 2, 15)

    def test_calculate_next_monthly_end_of_month(self):
        freq = RecurrenceFrequency("monthly")
        assert freq.calculate_next_date(date(2026, 1, 31)) == date(2026, 2, 28)

    def test_calculate_next_quarterly(self):
        freq = RecurrenceFrequency("quarterly")
        assert freq.calculate_next_date(date(2026, 1, 1)) == date(2026, 4, 1)

    def test_calculate_next_yearly(self):
        freq = RecurrenceFrequency("yearly")
        assert freq.calculate_next_date(date(2026, 6, 15)) == date(2027, 6, 15)

    def test_interval_2_monthly(self):
        freq = RecurrenceFrequency("monthly")
        assert freq.calculate_next_date(date(2026, 1, 1), interval=2) == date(2026, 3, 1)


class TestAuditAction:
    def test_valid_actions(self):
        for a in ["created", "updated", "deleted", "restored"]:
            assert AuditAction(a).value == a

    def test_invalid_action(self):
        with pytest.raises(ValueError):
            AuditAction("modified")
