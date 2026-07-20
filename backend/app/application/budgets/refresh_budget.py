"""Use case: Refresh/recalculate a budget's spent amount from transactions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RefreshBudgetUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        budget = await self._repo.recalculate_spent(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget")

        new_alerts = await self._repo.check_and_create_alerts(user_id)

        pct_used = (float(budget.spent) / float(budget.amount) * 100) if float(budget.amount) > 0 else 0

        return {
            "id": str(budget.id),
            "name": budget.name,
            "amount": str(budget.amount),
            "spent": str(budget.spent),
            "remaining": str(budget.remaining),
            "pct_used": round(pct_used, 1),
            "status": "exceeded" if pct_used > 100 else "warning" if pct_used >= budget.alert_threshold else "ok",
            "new_alerts": len(new_alerts),
        }
