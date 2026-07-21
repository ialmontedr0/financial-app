"""Use case: Predict next month's expenses."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class PredictExpensesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, *, months_ahead: int = 1) -> dict:
        """Predict next month's total expenses using XGBoost."""
        from app.ai.predictors.expense_predictor import ExpensePredictor
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)
        predictor = ExpensePredictor()
        predictor._target_type = "expense"
        predictor._model_version = "xgb_expense_v1.0"

        if not predictor.is_trained:
            predictor.load_model(str(user_id))

        if not predictor.is_trained:
            return {
                "predicted_amount": 0.0,
                "confidence": 0.0,
                "model_version": "none",
                "reason": "Model not trained. Run training first.",
                "features_used": {},
            }

        result = await predictor.predict(self._session, user_id, months_ahead=months_ahead)

        # Log prediction
        await repo.create_prediction(
            user_id,
            prediction_type="expense_forecast",
            model_version=result["model_version"],
            confidence=Decimal(str(result["confidence"])),
            predicted_amount=Decimal(str(result["predicted_amount"])),
            reason=result["reason"],
            features_used=result["features_used"],
        )

        return result
