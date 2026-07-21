"""Get monthly KPIs."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.analytics_repository import AnalyticsRepository

logger = structlog.get_logger()


class GetMonthlyKPIsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)

    async def execute(
        self, user_id: uuid.UUID, year: int | None = None, month: int | None = None
    ) -> dict:
        from datetime import date

        today = date.today()
        y = year or today.year
        m = month or today.month
        return await self._repo.get_monthly_kpis(user_id, y, m)
