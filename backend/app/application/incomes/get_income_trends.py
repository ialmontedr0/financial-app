"""Use case: Get income trends over months."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetIncomeTrendsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(self, user_id: uuid.UUID, *, months: int = 12) -> dict:
        from app.middleware.error_handler import ValidationError

        if months < 1 or months > 60:
            raise ValidationError("months debe estar entre 1 y 60")

        trends = await self._repo.get_income_trends(user_id, months=months)
        return trends
