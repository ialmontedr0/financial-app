"""Use case: Get aggregated budget summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetBudgetSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        summary = await self._repo.get_budget_summary(user_id)

        unread_count = await self._repo.get_unread_alert_count(user_id)
        new_alerts = await self._repo.check_and_create_alerts(user_id)

        return {
            **summary,
            "unread_alerts": unread_count,
            "new_alerts_triggered": len(new_alerts),
        }
