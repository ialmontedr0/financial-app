"""Use case: Get expense dashboard with analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetExpenseDashboardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, *, date_from: date, date_to: date) -> dict:
        from app.middleware.error_handler import ValidationError

        if date_from > date_to:
            raise ValidationError("date_from no puede ser posterior a date_to")

        dashboard = await self._repo.get_expense_dashboard(user_id, date_from, date_to)
        return dashboard
