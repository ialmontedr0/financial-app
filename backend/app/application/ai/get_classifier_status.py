"""Use case: Get classifier training status."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetClassifierStatusUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Return current classifier status and model info."""
        from app.ai.classifiers.ml_classifier import classifier
        from app.infrastructure.repositories.ai_repository import AIRepository

        repo = AIRepository(self._session)

        # Try to load user's model
        if not classifier.is_trained:
            classifier.load_model(str(user_id))

        # Get latest model from registry
        models = await repo.list_models(user_id, model_type="classifier_tfidf_lsvc")
        latest = models[0] if models else None

        return {
            "is_trained": classifier.is_trained,
            "model_version": classifier.model_version,
            "latest_model": {
                "id": str(latest.id) if latest else None,
                "status": latest.status if latest else None,
                "accuracy": str(latest.accuracy) if latest and latest.accuracy else None,
                "training_samples": latest.training_samples if latest else 0,
                "created_at": latest.created_at.isoformat()
                if latest and latest.created_at
                else None,
            }
            if latest
            else None,
            "total_models": len(models),
        }
