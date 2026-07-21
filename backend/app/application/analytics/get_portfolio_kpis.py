"""Get portfolio-level KPIs."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.analytics_repository import AnalyticsRepository

logger = structlog.get_logger()


class GetPortfolioKPIsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = AnalyticsRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        return await self._repo.get_portfolio_kpis(user_id)
