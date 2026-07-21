"""Get spending/income breakdown by category."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.analytics_repository import AnalyticsRepository

logger = structlog.get_logger()


class GetCategoryBreakdownUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        start_date: str | None = None,
        end_date: str | None = None,
        transaction_type: str = "expense",
    ) -> dict:
        if start_date:
            start = date.fromisoformat(start_date)
        else:
            start = date.today().replace(day=1)
        if end_date:
            end = date.fromisoformat(end_date)
        else:
            end = date.today()
        return await self._repo.get_category_breakdown(user_id, start, end, transaction_type)
