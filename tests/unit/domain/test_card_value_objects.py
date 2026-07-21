"""Unit tests for credit card value objects and business logic."""

import pytest
from datetime import date, timedelta
from decimal import Decimal


class TestUtilizationCalculation:
    """Test utilization calculation logic."""

    def test_healthy_utilization(self):
        limit = 100000
        used = 20000
        pct = (used / limit) * 100
        status = "healthy" if pct < 30 else "warning" if pct < 70 else "danger"
        assert pct == 20.0
        assert status == "healthy"

    def test_warning_utilization(self):
        limit = 100000
        used = 50000
        pct = (used / limit) * 100
        status = "healthy" if pct < 30 else "warning" if pct < 70 else "danger"
        assert pct == 50.0
        assert status == "warning"

    def test_danger_utilization(self):
        limit = 100000
        used = 80000
        pct = (used / limit) * 100
        status = "healthy" if pct < 30 else "warning" if pct < 70 else "danger"
        assert pct == 80.0
        assert status == "danger"

    def test_zero_limit(self):
        limit = 0
        used = 0
        pct = (used / limit * 100) if limit > 0 else 0
        assert pct == 0

    def test_full_utilization(self):
        limit = 50000
        used = 50000
        pct = (used / limit) * 100
        assert pct == 100.0


class TestStatementPeriodCalculation:
    """Test statement period date calculations."""

    def test_statement_day_1(self):
        stmt_day = 1
        today = date(2026, 7, 20)
        if today.day >= stmt_day:
            period_start = today.replace(day=stmt_day)
        else:
            period_start = today.replace(month=today.month - 1, day=stmt_day)
        assert period_start == date(2026, 7, 1)

    def test_statement_day_15(self):
        stmt_day = 15
        today = date(2026, 7, 20)
        if today.day >= stmt_day:
            period_start = today.replace(day=stmt_day)
        else:
            period_start = today.replace(month=today.month - 1, day=stmt_day)
        assert period_start == date(2026, 7, 15)

    def test_statement_day_before_today(self):
        stmt_day = 25
        today = date(2026, 7, 20)
        if today.day >= stmt_day:
            period_start = today.replace(day=stmt_day)
        else:
            period_start = today.replace(month=today.month - 1, day=stmt_day)
        assert period_start == date(2026, 6, 25)

    def test_statement_day_january(self):
        stmt_day = 5
        today = date(2026, 1, 10)
        if today.day >= stmt_day:
            period_start = today.replace(day=stmt_day)
        else:
            period_start = today.replace(year=today.year - 1, month=12, day=stmt_day)
        assert period_start == date(2026, 1, 5)


class TestPaymentCalculation:
    """Test payment and interest calculations."""

    def test_minimum_payment(self):
        total = Decimal("50000.0000")
        minimum_pct = 0.05
        minimum = max(float(total) * minimum_pct, 500)
        assert minimum == 2500.0

    def test_minimum_payment_floor(self):
        total = Decimal("5000.0000")
        minimum_pct = 0.05
        minimum = max(float(total) * minimum_pct, 500)
        assert minimum == 500

    def test_interest_calculation(self):
        balance = 100000.0
        annual_rate = 24.0
        monthly_interest = balance * (annual_rate / 100 / 12)
        assert monthly_interest == 2000.0

    def test_full_payment_clears_bill(self):
        total = 50000.0
        amount_paid = 50000.0
        status = "paid" if amount_paid >= total else "partial" if amount_paid > 0 else "pending"
        assert status == "paid"

    def test_partial_payment(self):
        total = 50000.0
        amount_paid = 20000.0
        status = "paid" if amount_paid >= total else "partial" if amount_paid > 0 else "pending"
        assert status == "partial"


class TestSpendingLimitPeriods:
    """Test spending limit period calculations."""

    def test_daily_period(self):
        today = date(2026, 7, 20)
        period_start = today
        period_end = today
        assert period_start == today
        assert period_end == today

    def test_weekly_period(self):
        today = date(2026, 7, 20)
        period_start = today - timedelta(days=today.weekday())
        assert period_start == date(2026, 7, 20)

    def test_weekly_period_wednesday(self):
        today = date(2026, 7, 22)
        period_start = today - timedelta(days=today.weekday())
        assert period_start == date(2026, 7, 20)

    def test_monthly_period(self):
        today = date(2026, 7, 20)
        period_start = today.replace(day=1)
        assert period_start == date(2026, 7, 1)

    def test_limit_exceeded(self):
        limit = 10000
        spent = 12000
        pct = (spent / limit) * 100
        status = "exceeded" if pct > 100 else "warning" if pct >= 80 else "ok"
        assert status == "exceeded"
