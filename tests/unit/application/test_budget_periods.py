"""Unit tests for budget period date helpers."""

from datetime import date

from app.application.budgets.periods import next_period_dates, resolve_period_end


class TestResolvePeriodEnd:
    def test_weekly(self):
        assert resolve_period_end("weekly", date(2026, 7, 20)) == date(2026, 7, 26)

    def test_biweekly(self):
        assert resolve_period_end("biweekly", date(2026, 7, 20)) == date(2026, 8, 2)

    def test_monthly(self):
        assert resolve_period_end("monthly", date(2026, 7, 1)) == date(2026, 7, 31)

    def test_monthly_december_wraps_year(self):
        assert resolve_period_end("monthly", date(2026, 12, 1)) == date(2026, 12, 31)

    def test_quarterly(self):
        assert resolve_period_end("quarterly", date(2026, 7, 1)) == date(2026, 9, 30)

    def test_yearly(self):
        assert resolve_period_end("yearly", date(2026, 1, 1)) == date(2026, 12, 31)


class TestNextPeriodDates:
    def test_monthly_next_period(self):
        start, end = next_period_dates("monthly", date(2026, 7, 31))
        assert start == date(2026, 8, 1)
        assert end == date(2026, 8, 31)

    def test_monthly_next_period_leap_year(self):
        start, end = next_period_dates("monthly", date(2028, 1, 31))
        assert start == date(2028, 2, 1)
        assert end == date(2028, 2, 29)

    def test_weekly_next_period(self):
        start, end = next_period_dates("weekly", date(2026, 7, 26))
        assert start == date(2026, 7, 27)
        assert end == date(2026, 8, 2)

    def test_yearly_next_period(self):
        start, end = next_period_dates("yearly", date(2026, 12, 31))
        assert start == date(2027, 1, 1)
        assert end == date(2027, 12, 31)
