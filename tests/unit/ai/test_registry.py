"""Tests for predictor registry."""

from __future__ import annotations

import pytest

from app.ai.predictors.expense_predictor import ExpensePredictor
from app.ai.predictors.lightgbm_predictor import LightGBMPredictor
from app.ai.predictors.registry import create_predictor


class TestPredictorRegistry:
    def test_create_xgboost_predictor(self):
        predictor = create_predictor("xgb_expense_v1.0")
        assert isinstance(predictor, ExpensePredictor)

    def test_create_xgboost_income(self):
        predictor = create_predictor("xgb_income_v1.0")
        assert isinstance(predictor, ExpensePredictor)

    def test_create_lightgbm_predictor(self):
        predictor = create_predictor("lgbm_expense_v1.0")
        assert isinstance(predictor, LightGBMPredictor)

    def test_create_lightgbm_income(self):
        predictor = create_predictor("lgbm_income_v1.0")
        assert isinstance(predictor, LightGBMPredictor)

    def test_default_to_xgboost_for_unknown(self):
        predictor = create_predictor("unknown_version")
        assert isinstance(predictor, ExpensePredictor)

    def test_default_to_xgboost_for_empty(self):
        predictor = create_predictor("")
        assert isinstance(predictor, ExpensePredictor)


class TestLightGBMPredictor:
    def test_initial_state(self):
        p = LightGBMPredictor()
        assert p.is_trained is False
        assert p.model_version == "lgbm_expense_v1.0"

    def test_target_type_default(self):
        p = LightGBMPredictor()
        assert p._target_type == "expense"

    def test_model_version_setter(self):
        p = LightGBMPredictor()
        p._model_version = "lgbm_income_v1.0"
        assert p.model_version == "lgbm_income_v1.0"

    async def test_predict_not_trained(self):
        p = LightGBMPredictor()
        result = await p.predict(None, "user-1")  # type: ignore
        assert result["predicted_amount"] == 0.0
        assert result["confidence"] == 0.0
        assert result["model_version"] == "none"
        assert "not trained" in result["reason"].lower()

    async def test_predict_not_trained_no_session(self):
        """Predict should handle None session gracefully when not trained."""
        p = LightGBMPredictor()
        # Should not raise even with None session since it checks is_trained first
        result = await p.predict(None, "user-1")  # type: ignore
        assert "error" not in result
