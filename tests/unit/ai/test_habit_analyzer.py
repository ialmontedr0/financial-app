"""Tests for habit analyzer."""

import pytest
from app.ai.recommendations.habit_analyzer import HabitAnalyzer


class TestHabitAnalyzer:
    def test_frequency_label(self):
        analyzer = HabitAnalyzer()
        assert analyzer._frequency_label(7) == "diario"
        assert analyzer._frequency_label(3) == "frecuente"
        assert analyzer._frequency_label(1) == "regular"
        assert analyzer._frequency_label(0.3) == "ocasional"
        assert analyzer._frequency_label(0) == "sin actividad"

    def test_habit_score(self):
        analyzer = HabitAnalyzer()
        frequency = {}
        stability = {
            "cat1": {"label": "estable"},
            "cat2": {"label": "muy_estable"},
            "cat3": {"label": "muy_variable"},
        }
        dominance = {
            "cat1": {"is_dominant": False},
            "cat2": {"is_dominant": False},
            "cat3": {"is_dominant": True},
        }
        score = analyzer._compute_habit_score(frequency, stability, dominance)
        assert 0 <= score <= 100

    def test_frequency_label_edge_cases(self):
        analyzer = HabitAnalyzer()
        assert analyzer._frequency_label(0.01) == "ocasional"
        assert analyzer._frequency_label(10) == "diario"