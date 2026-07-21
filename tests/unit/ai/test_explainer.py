"""Tests for personalized explainer."""

import pytest
from app.ai.recommendations.explainer import Explainer


class TestExplainer:
    def test_fallback_explanation(self):
        explainer = Explainer()
        rec = {
            "type": "unknown_type",
            "title": "Test Rec",
            "description": "Test description",
            "priority": "medium",
            "estimated_savings": 1000,
            "confidence": 0.7,
        }
        result = explainer._fallback_explanation(rec)
        assert result["headline"] == "Test Rec"
        assert result["personalized"] is False

    def test_fill_template_simple(self):
        explainer = Explainer()
        template = "Gastaste {amount:.0f} este mes."
        features = {"amount": 5000}
        result = explainer._fill_template(template, features)
        assert result == "Gastaste 5000 este mes."

    def test_fill_template_with_computed(self):
        explainer = Explainer()
        template = "Ahorro anual: {annual:.0f}"
        features = {"savings": 1000}
        result = explainer._fill_template(template, features)
        assert result == "Ahorro anual: 12000"
