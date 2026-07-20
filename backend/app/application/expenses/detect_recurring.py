"""Use case: Detect recurring expense candidates (expenses that repeat)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DetectRecurringUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        candidates = await self._repo.detect_recurring_candidates(user_id)

        monthly_like = [c for c in candidates if c.get("is_monthly_like")]
        non_monthly = [c for c in candidates if not c.get("is_monthly_like")]

        # Estimate monthly cost from monthly-like candidates
        from decimal import Decimal

        estimated_monthly = sum(Decimal(c["amount"]) for c in monthly_like)

        return {
            "total_candidates": len(candidates),
            "monthly_like_count": len(monthly_like),
            "non_monthly_count": len(non_monthly),
            "estimated_monthly_from_recurring": str(round(float(estimated_monthly), 2)),
            "candidates": candidates,
        }
