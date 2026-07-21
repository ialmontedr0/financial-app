"""Use case: Classify multiple transactions in batch."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ClassifyBatchUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        transaction_ids: list[str] | None = None,
    ) -> dict:
        """Classify all unclassified transactions for a user.

        If transaction_ids is provided, only classify those.
        Otherwise, classify the last 50 transactions without AI classification.
        """
        from sqlalchemy import and_, select

        from app.ai.classifiers.ml_classifier import classifier
        from app.infrastructure.models.transaction import TransactionModel
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)

        if not classifier.is_trained:
            classifier.load_model(str(user_id))

        if not classifier.is_trained:
            return {
                "classified": 0,
                "model_version": "none",
                "reason": "Model not trained. Run training first.",
                "results": [],
            }

        # Fetch transactions to classify
        stmt = (
            select(TransactionModel)
            .where(
                and_(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.status == "completed",
                    TransactionModel.transaction_type.in_(["expense", "income"]),
                    TransactionModel.ai_category_id.is_(None),  # not yet classified
                )
            )
            .order_by(TransactionModel.effective_date.desc())
            .limit(50)
        )
        result = await self._session.execute(stmt)
        transactions = list(result.scalars().all())

        classified = 0
        results = []

        for tx in transactions:
            prediction = await classifier.predict(tx.description)
            if prediction is None:
                continue

            await repo.create_prediction(
                user_id,
                prediction_type="classification",
                model_version=prediction["model_version"],
                confidence=Decimal(str(prediction["confidence"])),
                predicted_value=prediction["category_slug"],
                reason=f"Batch classification: {prediction['category_slug']}",
                features_used={"features": prediction["features_used"]},
                transaction_id=tx.id,
            )
            classified += 1
            results.append(
                {
                    "transaction_id": str(tx.id),
                    "description": tx.description,
                    "predicted_category": prediction["category_slug"],
                    "confidence": prediction["confidence"],
                }
            )

        return {
            "classified": classified,
            "total_checked": len(transactions),
            "model_version": classifier.model_version,
            "results": results,
        }
