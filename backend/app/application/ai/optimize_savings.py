"""Use case: Generate savings optimization recommendations."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class OptimizeSavingsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Run savings optimization."""
        from app.ai.recommendations.savings_optimizer import SavingsOptimizer

        optimizer = SavingsOptimizer()
        return await optimizer.optimize(self._session, user_id)
