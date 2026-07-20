"""Use case: Auto-detect recurring income patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AutoDetectRecurringUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        candidates = await self._repo.detect_recurring_incomes(user_id)

        monthly_like = [c for c in candidates if c.get("is_monthly_like")]
        other = [c for c in candidates if not c.get("is_monthly_like")]

        return {
            "total_candidates": len(candidates),
            "monthly_like_count": len(monthly_like),
            "monthly_like": monthly_like,
            "other_patterns": other,
        }
