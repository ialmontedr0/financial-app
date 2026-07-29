"""Use case: Get latest generated recommendations with staleness check."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetLatestRecommendationsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Return the latest batch of recommendations and whether new data exists."""
        from datetime import UTC, datetime

        from sqlalchemy import func, select
        from sqlalchemy.orm import load_only

        from app.infrastructure.models.ai_prediction import AIPredictionModel
        from app.infrastructure.models.transaction import TransactionModel

        # Get latest batch
        stmt = (
            select(AIPredictionModel)
            .where(
                AIPredictionModel.user_id == user_id,
                AIPredictionModel.prediction_type == "recommendation_batch",
            )
            .order_by(AIPredictionModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        batch = result.scalar_one_or_none()

        if batch is None or batch.metadata_json is None:
            return {
                "recommendations": [],
                "total": 0,
                "high_priority": 0,
                "estimated_total_savings": 0,
                "last_generated_at": None,
                "has_new_transactions": False,
                "has_batch": False,
            }

        recommendations = batch.metadata_json.get("recommendations", [])
        features = batch.features_used or {}

        # Check if new transactions exist since batch was created
        batch_created = batch.created_at.replace(tzinfo=UTC)
        tx_stmt = select(func.count()).select_from(
            select(TransactionModel)
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.created_at > batch_created,
            )
            .subquery()
        )
        tx_count = (await self._session.execute(tx_stmt)).scalar() or 0

        return {
            "recommendations": recommendations,
            "total": features.get("total", len(recommendations)),
            "high_priority": features.get(
                "high_priority",
                sum(1 for r in recommendations if r.get("priority") == "high"),
            ),
            "estimated_total_savings": features.get(
                "estimated_total_savings",
                round(sum(r.get("estimated_savings", 0) for r in recommendations), 2),
            ),
            "last_generated_at": batch.created_at.isoformat() if batch.created_at else None,
            "has_new_transactions": tx_count > 0,
            "has_batch": True,
        }
