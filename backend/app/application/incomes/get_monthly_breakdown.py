"""Use case: Get monthly income breakdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetMonthlyBreakdownUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(self, user_id: uuid.UUID, *, year: int, month: int) -> dict:
        from app.middleware.error_handler import ValidationError

        if month < 1 or month > 12:
            raise ValidationError("month debe estar entre 1 y 12")
        if year < 2000 or year > 2100:
            raise ValidationError("year no valido")

        breakdown = await self._repo.get_monthly_breakdown(user_id, year, month)
        return breakdown
