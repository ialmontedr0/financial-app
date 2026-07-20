"""Use case: Update a budget."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateBudgetUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(
        self, user_id: uuid.UUID, budget_id: uuid.UUID, *, changes: dict[str, Any]
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        allowed_fields = {
            "name", "description", "amount", "alert_threshold", "alert_enabled",
            "auto_adjust", "rollover", "strategy", "is_active", "icon", "color",
        }
        filtered = {k: v for k, v in changes.items() if k in allowed_fields}

        if "amount" in filtered:
            try:
                filtered["amount"] = float(filtered["amount"])
            except (TypeError, ValueError):
                pass
            if filtered["amount"] <= 0:
                raise ValidationError("amount debe ser mayor a 0")

        if "alert_threshold" in filtered:
            if not (1 <= filtered["alert_threshold"] <= 100):
                raise ValidationError("alert_threshold debe ser entre 1 y 100")

        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_budget(budget_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("Budget")

        updated = await self._repo.recalculate_spent(budget_id, user_id) or updated

        pct_used = (float(updated.spent) / float(updated.amount) * 100) if float(updated.amount) > 0 else 0

        return {
            "id": str(updated.id),
            "name": updated.name,
            "description": updated.description,
            "budget_type": updated.budget_type,
            "amount": str(updated.amount),
            "spent": str(updated.spent),
            "remaining": str(updated.remaining),
            "period": updated.period,
            "start_date": updated.start_date.isoformat(),
            "end_date": updated.end_date.isoformat(),
            "category_id": str(updated.category_id) if updated.category_id else None,
            "account_id": str(updated.account_id) if updated.account_id else None,
            "alert_threshold": updated.alert_threshold,
            "alert_enabled": updated.alert_enabled,
            "auto_adjust": updated.auto_adjust,
            "rollover": updated.rollover,
            "strategy": updated.strategy,
            "is_active": updated.is_active,
            "pct_used": round(pct_used, 1),
            "icon": updated.icon,
            "color": updated.color,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
