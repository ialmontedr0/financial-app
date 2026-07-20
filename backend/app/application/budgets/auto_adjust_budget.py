"""Use case: Auto-adjust a budget based on historical spending."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AutoAdjustBudgetUseCase:
    """Suggest automatic budget adjustments based on 3-month spending history."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        budget_id: uuid.UUID,
        *,
        buffer_pct: float = 10.0,
        apply: bool = False,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        budget = await self._repo.get_budget_by_id(budget_id, user_id)
        if budget is None:
            raise NotFoundError("Budget")

        if not budget.auto_adjust:
            raise ValidationError("Auto-adjustment not enabled for this budget")

        historical = await self._repo.get_monthly_spending(
            user_id,
            category_id=budget.category_id if budget.budget_type == "category" else None,
        )

        if not historical:
            return {
                "message": "No historical data found for adjustment",
                "current_amount": str(budget.amount),
                "suggested_amount": str(budget.amount),
            }

        amounts = [float(h["total"]) for h in historical if float(h["total"]) > 0]
        if not amounts:
            return {
                "message": "No spending history found",
                "current_amount": str(budget.amount),
                "suggested_amount": str(budget.amount),
            }

        avg = sum(amounts) / len(amounts)
        suggested = avg * (1 + buffer_pct / 100)

        result = {
            "current_amount": str(budget.amount),
            "average_spending": str(round(avg, 2)),
            "suggested_amount": str(round(suggested, 2)),
            "buffer_pct": buffer_pct,
            "periods_analyzed": len(amounts),
            "applied": False,
        }

        if apply:
            old_amount = float(budget.amount)
            await self._repo.update_budget(budget_id, user_id, amount=suggested)
            budget = await self._repo.get_budget_by_id(budget_id, user_id)
            history = budget.adjustment_history if budget and budget.adjustment_history else []
            history = list(history) if history else []
            history.append({
                "old_amount": old_amount,
                "new_amount": suggested,
                "avg_spending": avg,
                "buffer_pct": buffer_pct,
                "date": str(__import__("datetime").date.today()),  # noqa: DTZ011
                "reason": "auto_adjust",
            })
            await self._repo.update_budget(budget_id, user_id, adjustment_history=history)
            result["applied"] = True
            result["new_amount"] = str(round(suggested, 2))

        return result
