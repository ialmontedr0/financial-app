"""Tests for savings optimizer."""

import pytest
from app.ai.recommendations.savings_optimizer import SavingsOptimizer


class TestSavingsOptimizer:
    def test_simulate_debt_payoff(self):
        optimizer = SavingsOptimizer()
        loans = [
            {"balance": 10000, "interest_rate": 12, "monthly_payment": 500},
            {"balance": 5000, "interest_rate": 24, "monthly_payment": 300},
        ]
        total_interest = optimizer._simulate_debt_payoff(loans)
        assert total_interest > 0

    def test_simulate_debt_payoff_empty(self):
        optimizer = SavingsOptimizer()
        total_interest = optimizer._simulate_debt_payoff([])
        assert total_interest == 0
