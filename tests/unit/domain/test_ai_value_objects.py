"""Unit tests for AI domain value objects."""

import pytest

from app.domain.ai.value_objects import (
    AnomalySeverity,
    ModelType,
    PredictionType,
    RecommendationType,
    TrainingStatus,
)


class TestPredictionType:
    def test_valid_types(self):
        for t in [
            "expense_forecast",
            "income_forecast",
            "anomaly",
            "classification",
            "recommendation",
            "goal_forecast",
        ]:
            pt = PredictionType(t)
            assert pt.value == t

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Tipo de prediccion no soportado"):
            PredictionType("invalid")

    def test_name(self):
        pt = PredictionType("anomaly")
        assert pt.name == "Anomalia Detectada"


class TestModelType:
    def test_valid_types(self):
        for t in [
            "classifier_tfidf_lsvc",
            "expense_predictor_xgboost",
            "anomaly_isolation_forest",
            "anomaly_autoencoder",
        ]:
            mt = ModelType(t)
            assert mt.value == t

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="Tipo de modelo no soportado"):
            ModelType("random_forest")


class TestAnomalySeverity:
    def test_valid(self):
        for s in ["low", "medium", "high", "critical"]:
            sev = AnomalySeverity(s)
            assert sev.value == s

    def test_invalid(self):
        with pytest.raises(ValueError, match="Severidad no soportada"):
            AnomalySeverity("extreme")


class TestRecommendationType:
    def test_valid(self):
        for r in ["reduce_spending", "increase_savings", "cancel_subscription", "pay_debt"]:
            rt = RecommendationType(r)
            assert rt.value == r

    def test_invalid(self):
        with pytest.raises(ValueError, match="Tipo de recomendacion no soportado"):
            RecommendationType("invest")


class TestTrainingStatus:
    def test_valid(self):
        for s in ["pending", "training", "completed", "failed", "deprecated"]:
            ts = TrainingStatus(s)
            assert ts.value == s
