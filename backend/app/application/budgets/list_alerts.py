"""Use case: List budget alerts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListAlertsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        budget_id: uuid.UUID | None = None,
        is_read: bool | None = None,
        alert_type: str | None = None,
        severity: str | None = None,
    ) -> dict:
        alerts = await self._repo.list_alerts(
            user_id,
            budget_id=budget_id,
            is_read=is_read,
            alert_type=alert_type,
            severity=severity,
        )

        items = [
            {
                "id": str(a.id),
                "budget_id": str(a.budget_id),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "threshold_percentage": a.threshold_percentage,
                "current_amount": str(a.current_amount) if a.current_amount else None,
                "budget_amount": str(a.budget_amount) if a.budget_amount else None,
                "is_read": a.is_read,
                "is_dismissed": a.is_dismissed,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            }
            for a in alerts
        ]

        return {"alerts": items, "total": len(items)}
