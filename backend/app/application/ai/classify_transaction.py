"""Use case: Classify a single transaction."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ClassifyTransactionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        transaction_id: uuid.UUID,
        description: str,
        category_id: uuid.UUID | None = None,
    ) -> dict:
        from app.ai.classifiers.ml_classifier import classifier
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)

        # Try to load model if not loaded
        if not classifier.is_trained:
            classifier.load_model(str(user_id))

        # Predict
        result = await classifier.predict(description)

        if result is None:
            return {
                "predicted_category": None,
                "confidence": 0.0,
                "model_version": "none",
                "reason": "Model not trained. Run training first.",
                "features_used": {},
            }

        # Log prediction
        await repo.create_prediction(
            user_id,
            prediction_type="classification",
            model_version=result["model_version"],
            confidence=Decimal(str(result["confidence"])),
            predicted_value=result["category_slug"],
            reason=f"Clasificacion automatica: {result['category_slug']} (confianza: {result['confidence']:.2%})",
            features_used={"features": result["features_used"]},
            transaction_id=transaction_id,
        )

        return {
            "predicted_category": result["category_slug"],
            "confidence": result["confidence"],
            "model_version": result["model_version"],
            "reason": f"Clasificacion automatica basada en descripcion",
            "features_used": result["features_used"],
        }
