"""Use case: List budgets with filters."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListBudgetsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        budget_type: str | None = None,
        is_active: bool | None = None,
        period: str | None = None,
    ) -> dict:
        budgets = await self._repo.list_budgets(
            user_id, budget_type=budget_type, is_active=is_active, period=period
        )

        items = []
        for b in budgets:
            if b.is_active:
                b = await self._repo.recalculate_spent(b.id, user_id) or b

            pct_used = (float(b.spent) / float(b.amount) * 100) if float(b.amount) > 0 else 0

            items.append({
                "id": str(b.id),
                "name": b.name,
                "description": b.description,
                "budget_type": b.budget_type,
                "amount": str(b.amount),
                "spent": str(b.spent),
                "remaining": str(b.remaining),
                "period": b.period,
                "start_date": b.start_date.isoformat(),
                "end_date": b.end_date.isoformat(),
                "category_id": str(b.category_id) if b.category_id else None,
                "account_id": str(b.account_id) if b.account_id else None,
                "alert_threshold": b.alert_threshold,
                "alert_enabled": b.alert_enabled,
                "auto_adjust": b.auto_adjust,
                "rollover": b.rollover,
                "strategy": b.strategy,
                "is_active": b.is_active,
                "pct_used": round(pct_used, 1),
                "status": "exceeded" if pct_used > 100 else "warning" if pct_used >= b.alert_threshold else "ok",
                "icon": b.icon,
                "color": b.color,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            })

        return {"budgets": items, "total": len(items)}
