"""Use case: Assess user financial risks."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AssessRisksUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Run full risk assessment."""
        from app.ai.recommendations.risk_assessor import RiskAssessor

        assessor = RiskAssessor()
        return await assessor.assess(self._session, user_id)
