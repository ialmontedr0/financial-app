"""Use case: Quick financial health score."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetHealthScoreUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Get quick health score."""
        from app.ai.recommendations.risk_assessor import RiskAssessor

        assessor = RiskAssessor()
        return await assessor.get_health_score(self._session, user_id)