"""Get spending trend over time."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.analytics_repository import AnalyticsRepository

logger = structlog.get_logger()


class GetSpendingTrendUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str = "monthly",
    ) -> dict:
        if start_date:
            start = date.fromisoformat(start_date)
        else:
            start = date.today() - timedelta(days=180)
        if end_date:
            end = date.fromisoformat(end_date)
        else:
            end = date.today()
        return await self._repo.get_spending_trend(user_id, start, end, period)
