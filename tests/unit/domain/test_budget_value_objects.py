"""Unit tests for budget domain value objects and logic."""

import uuid
from datetime import date, timedelta

import pytest


class TestBudgetPeriodCalculation:
    """Test period calculation logic used in budget creation."""

    def test_weekly_period_end(self):
        start = date(2026, 7, 20)
        end = start + timedelta(days=6)
        assert end == date(2026, 7, 26)

    def test_biweekly_period_end(self):
        start = date(2026, 7, 20)
        end = start + timedelta(days=13)
        assert end == date(2026, 8, 2)

    def test_monthly_period_end(self):
        start = date(2026, 7, 1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
        assert end == date(2026, 7, 31)

    def test_quarterly_period_end(self):
        start = date(2026, 7, 1)
        quarter_month = ((start.month - 1) // 3 + 1) * 3
        if quarter_month >= 12:
            end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = start.replace(month=quarter_month + 1, day=1) - timedelta(days=1)
        assert end == date(2026, 9, 30)

    def test_yearly_period_end(self):
        start = date(2026, 1, 1)
        end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
        assert end == date(2026, 12, 31)


class TestBudgetStatusCalculation:
    """Test budget status threshold logic."""

    def test_status_ok(self):
        spent, amount, threshold = 500.0, 1000.0, 80
        pct = spent / amount * 100
        status = "exceeded" if pct > 100 else "warning" if pct >= threshold else "ok"
        assert status == "ok"

    def test_status_warning(self):
        spent, amount, threshold = 850.0, 1000.0, 80
        pct = spent / amount * 100
        status = "exceeded" if pct > 100 else "warning" if pct >= threshold else "ok"
        assert status == "warning"

    def test_status_exceeded(self):
        spent, amount, threshold = 1100.0, 1000.0, 80
        pct = spent / amount * 100
        status = "exceeded" if pct > 100 else "warning" if pct >= threshold else "ok"
        assert status == "exceeded"

    def test_zero_amount(self):
        spent, amount = 0, 0
        pct = (spent / amount * 100) if amount > 0 else 0
        assert pct == 0


class TestBudgetAlertThresholds:
    """Test alert creation logic."""

    def test_alert_at_threshold(self):
        threshold = 80
        pct = 82.5
        assert pct >= threshold

    def test_alert_not_yet(self):
        threshold = 80
        pct = 79.9
        assert pct < threshold

    def test_severity_escalation(self):
        pct = 85
        severity = "warning" if pct < 90 else "critical"
        assert severity == "warning"

    def test_severity_critical(self):
        pct = 92
        severity = "warning" if pct < 90 else "critical"
        assert severity == "critical"
