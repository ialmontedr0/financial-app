"""Use case: Get budget details with analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetBudgetUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(self, user_id: uuid.UUID, budget_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        budget = await self._repo.get_budget_by_id(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget")

        budget = await self._repo.recalculate_spent(budget_id, user_id) or budget

        pct_used = (float(budget.spent) / float(budget.amount) * 100) if float(budget.amount) > 0 else 0

        alerts = await self._repo.list_alerts(user_id, budget_id=budget_id)
        unread_alerts = sum(1 for a in alerts if not a.is_read and not a.is_dismissed)

        return {
            "id": str(budget.id),
            "name": budget.name,
            "description": budget.description,
            "budget_type": budget.budget_type,
            "amount": str(budget.amount),
            "spent": str(budget.spent),
            "remaining": str(budget.remaining),
            "period": budget.period,
            "start_date": budget.start_date.isoformat(),
            "end_date": budget.end_date.isoformat(),
            "category_id": str(budget.category_id) if budget.category_id else None,
            "account_id": str(budget.account_id) if budget.account_id else None,
            "alert_threshold": budget.alert_threshold,
            "alert_enabled": budget.alert_enabled,
            "auto_adjust": budget.auto_adjust,
            "rollover": budget.rollover,
            "strategy": budget.strategy,
            "adjustment_history": budget.adjustment_history,
            "is_active": budget.is_active,
            "pct_used": round(pct_used, 1),
            "status": "exceeded" if pct_used > 100 else "warning" if pct_used >= budget.alert_threshold else "ok",
            "icon": budget.icon,
            "color": budget.color,
            "unread_alerts": unread_alerts,
            "created_at": budget.created_at.isoformat() if budget.created_at else None,
        }
