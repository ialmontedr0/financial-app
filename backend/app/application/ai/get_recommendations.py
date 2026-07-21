"""Use case: Generate financial recommendations."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetRecommendationsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Generate personalized financial recommendations."""
        from app.ai.recommendations.engine import RecommendationEngine
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)
        engine = RecommendationEngine()

        recommendations = await engine.generate(self._session, user_id)

        # Log each recommendation as a prediction
        for rec in recommendations:
            await repo.create_prediction(
                user_id,
                prediction_type="recommendation",
                model_version="rule_engine_v1.0",
                confidence=Decimal(str(rec.get("confidence", 0))),
                predicted_value=rec.get("type"),
                reason=rec.get("description"),
                features_used=rec.get("features_used"),
            )

        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "high_priority": sum(1 for r in recommendations if r.get("priority") == "high"),
            "estimated_total_savings": round(
                sum(r.get("estimated_savings", 0) for r in recommendations), 2
            ),
        }
