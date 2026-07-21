"""Tests for Phase 16 value objects."""

import pytest
from app.domain.ai.value_objects import (
    RiskLevel,
    HabitType,
    OptimizationStrategy,
)


class TestRiskLevel:
    def test_valid_levels(self):
        for level in ("low", "medium", "high", "critical"):
            rl = RiskLevel(level)
            assert str(rl) == level

    def test_invalid_level(self):
        with pytest.raises(ValueError, match="Nivel de riesgo no soportado"):
            RiskLevel("extreme")

    def test_name_property(self):
        assert RiskLevel("high").name == "Alto"
        assert RiskLevel("critical").name == "Critico"


class TestHabitType:
    def test_valid_types(self):
        for htype in (
            "spending_frequency",
            "spending_amount",
            "income_regularity",
            "category_dominance",
            "weekend_spending",
            "payday_spending",
        ):
            ht = HabitType(htype)
            assert str(ht) == htype

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Tipo de habito no soportado"):
            HabitType("invalid")


class TestOptimizationStrategy:
    def test_valid_strategies(self):
        for strat in (
            "50_30_20",
            "debt_snowball",
            "debt_avalanche",
            "goal_first",
            "emergency_first",
            "balanced",
        ):
            os = OptimizationStrategy(strat)
            assert str(os) == strat

    def test_invalid_strategy(self):
        with pytest.raises(ValueError, match="Estrategia no soportada"):
            OptimizationStrategy("kelly_criterion")
