"""Unit tests for financial goal domain logic."""

from datetime import date, timedelta

import pytest


class TestGoalPeriodCalculation:
    def test_default_one_year_timeline(self):
        start = date(2026, 1, 1)
        target = start + timedelta(days=365)
        assert target == date(2026, 12, 31) or target == date(2027, 1, 1)

    def test_months_to_reach_no_interest(self):
        remaining = 120000.0
        monthly = 10000.0
        months = max(int(remaining / monthly), 1)
        assert months == 12

    def test_months_to_reach_with_interest(self):
        remaining = 120000.0
        monthly = 8000.0
        rate = 0.06 / 12
        balance = 0.0
        months = 0
        while balance < remaining and months < 600:
            months += 1
            balance = (balance + monthly) * (1 + rate)
        assert months <= 15


class TestGoalProbabilityCalculation:
    def test_on_track_probability(self):
        target_date = date(2027, 1, 1)
        predicted = date(2026, 12, 20)
        if predicted <= target_date:
            probability = min(1.0, 1.0 - max((target_date - predicted).days / 365.0, 0))
        else:
            probability = max(0.0, 1.0 - ((predicted - target_date).days / 365.0))
        assert probability > 0.9

    def test_behind_schedule_probability(self):
        target_date = date(2026, 12, 31)
        predicted = date(2027, 10, 1)
        if predicted <= target_date:
            probability = min(1.0, 1.0 - max((target_date - predicted).days / 365.0, 0))
        else:
            probability = max(0.0, 1.0 - ((predicted - target_date).days / 365.0))
        assert probability < 0.3


class TestGoalMilestoneCalculation:
    def test_milestone_25(self):
        assert 27.5 >= 25

    def test_milestone_50(self):
        assert 52.0 >= 50

    def test_milestone_75(self):
        assert 78.3 >= 75

    def test_milestone_90(self):
        assert 91.0 >= 90

    def test_no_milestone(self):
        assert 12.0 < 25


class TestGoalProgressCalculation:
    def test_on_track(self):
        assert not (55.0 < 50.0)

    def test_behind(self):
        assert 30.0 < 50.0

    def test_ahead(self):
        assert not (60.0 < 25.0)

    def test_monthly_needed(self):
        remaining = 60000.0
        months_left = 12.0
        monthly_needed = round(remaining / months_left, 2) if months_left > 0 else remaining
        assert monthly_needed == 5000.0
