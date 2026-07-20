"""Use case: Dismiss a budget alert."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DismissAlertUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(self, user_id: uuid.UUID, alert_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        success = await self._repo.dismiss_alert(alert_id, user_id)
        if not success:
            raise NotFoundError("Alert")

        return {"message": "Alert dismissed"}
