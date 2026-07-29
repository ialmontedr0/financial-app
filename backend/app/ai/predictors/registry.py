"""Predictor registry — factory for creating the right predictor by model version."""

from __future__ import annotations


def create_predictor(model_version: str):
    """Create a predictor instance based on model version prefix."""
    from app.ai.predictors.expense_predictor import ExpensePredictor
    from app.ai.predictors.lightgbm_predictor import LightGBMPredictor

    if model_version.startswith("lgbm_"):
        return LightGBMPredictor()
    return ExpensePredictor()
