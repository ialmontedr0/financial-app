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
        from app.application.notifications.helpers import mirror_inapp_notifications

        summary = await self._repo.get_budget_summary(user_id)

        unread_count = await self._repo.get_unread_alert_count(user_id)
        new_alerts = await self._repo.check_and_create_alerts(user_id)

        if new_alerts:
            await mirror_inapp_notifications(
                self._session,
                user_id,
                [
                    {
                        "type": "budget_warning" if a.severity == "critical" else "budget_alert",
                        "title": a.title,
                        "body": a.message,
                        "data": {"alert_id": str(a.id), "budget_id": str(a.budget_id)},
                    }
                    for a in new_alerts
                ],
            )

        return {
            **summary,
            "unread_alerts": unread_count,
            "new_alerts_triggered": len(new_alerts),
        }
