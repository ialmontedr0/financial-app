"""Use case: Simulate savings scenarios."""

from __future__ import annotations

import uuid

import structlog

if __name__ != "__main__":
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class SimulateSavingsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        monthly_amount: float,
        months: int = 12,
        annual_return_pct: float = 0.0,
    ) -> dict:
        """Simulate savings accumulation."""
        from app.ai.recommendations.savings_optimizer import SavingsOptimizer

        optimizer = SavingsOptimizer()
        return await optimizer.simulate(
            self._session, user_id,
            monthly_amount=monthly_amount,
            months=months,
            annual_return_pct=annual_return_pct,
        )