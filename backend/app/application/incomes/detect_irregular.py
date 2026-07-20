"""Use case: Detect irregularities in income patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DetectIrregularUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(self, user_id: uuid.UUID, *, months: int = 6) -> dict:
        irregularities = await self._repo.detect_irregular_income(user_id, months=months)

        return {
            "period_months": months,
            "irregularity_count": len(irregularities),
            "irregularities": irregularities,
        }
