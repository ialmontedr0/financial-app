"""Use case: Get personalized explanation for a recommendation."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetPersonalizedExplanationUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        recommendation: dict,
    ) -> dict:
        """Generate personalized explanation."""
        from app.ai.recommendations.explainer import Explainer

        explainer = Explainer()
        return await explainer.explain(self._session, user_id, recommendation)
