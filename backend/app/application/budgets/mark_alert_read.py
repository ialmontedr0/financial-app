"""Use case: Mark alert(s) as read."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class MarkAlertReadUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(
        self, user_id: uuid.UUID, alert_id: uuid.UUID | None = None, *, mark_all: bool = False
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        if mark_all:
            count = await self._repo.mark_all_alerts_read(user_id)
            return {"message": f"Marked {count} alerts as read", "count": count}

        if alert_id is None:
            raise ValidationError("alert_id es requerido o usa mark_all=true")

        success = await self._repo.mark_alert_read(alert_id, user_id)
        if not success:
            raise NotFoundError("Alert")

        return {"message": "Alert marked as read"}
