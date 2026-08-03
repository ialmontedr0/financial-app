"""Use case: Close expired budgets and roll over into the next period."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import structlog

from app.application.budgets.periods import next_period_dates
from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RolloverExpiredBudgetsUseCase:
    """Close budgets whose period ended and create the next period's budget.

    When ``rollover`` is enabled on the expiring budget, the unspent balance is
    carried over into the new budget's amount; otherwise the new budget starts
    from the same amount. A ``budget_closed`` notification is emitted for each
    closed budget.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        from datetime import date as date_type

        from app.application.notifications.helpers import mirror_inapp_notifications

        today = date_type.today()  # noqa: DTZ011
        expired = await self._repo.list_expired_active_budgets(user_id, today)

        closed: list[dict] = []
        notifications: list[dict] = []

        for budget in expired:
            budget = await self._repo.recalculate_spent(budget.id, user_id) or budget

            carry = max(budget.remaining, Decimal("0"))
            if not budget.rollover:
                carry = Decimal("0")

            next_start, next_end = next_period_dates(budget.period, budget.end_date)
            while next_end < today:
                next_start, next_end = next_period_dates(budget.period, next_end)

            budget.is_active = False
            budget.rollover_amount = carry
            await self._session.flush()

            new_amount = budget.amount + carry
            new_budget = await self._repo.create_budget(
                user_id,
                name=budget.name,
                description=budget.description,
                budget_type=budget.budget_type,
                amount=new_amount,
                spent=Decimal("0"),
                remaining=new_amount,
                period=budget.period,
                start_date=next_start,
                end_date=next_end,
                category_id=budget.category_id,
                account_id=budget.account_id,
                alert_threshold=budget.alert_threshold,
                alert_enabled=budget.alert_enabled,
                auto_adjust=budget.auto_adjust,
                rollover=budget.rollover,
                rollover_amount=carry,
                strategy=budget.strategy,
                is_active=True,
                icon=budget.icon,
                color=budget.color,
            )
            new_budget = await self._repo.recalculate_spent(new_budget.id, user_id) or new_budget

            if carry:
                body = (
                    f"El presupuesto '{budget.name}' cerró con un sobrante de "
                    f"${carry:,.2f} que se trasladó al siguiente período "
                    f"({next_start.isoformat()} a {next_end.isoformat()})."
                )
            else:
                body = (
                    f"El presupuesto '{budget.name}' cerró y se creó uno nuevo para el "
                    f"período ({next_start.isoformat()} a {next_end.isoformat()})."
                )

            notifications.append(
                {
                    "type": "budget_closed",
                    "title": f"Presupuesto cerrado: {budget.name}",
                    "body": body,
                    "data": {
                        "closed_budget_id": str(budget.id),
                        "new_budget_id": str(new_budget.id),
                        "start_date": next_start.isoformat(),
                        "end_date": next_end.isoformat(),
                        "carryover": str(carry),
                    },
                }
            )

            closed.append(
                {
                    "closed_budget_id": str(budget.id),
                    "new_budget_id": str(new_budget.id),
                    "name": budget.name,
                    "start_date": next_start.isoformat(),
                    "end_date": next_end.isoformat(),
                    "carryover": str(carry),
                }
            )

        if notifications:
            await mirror_inapp_notifications(self._session, user_id, notifications)
            logger.info("budgets_rolled_over", user_id=str(user_id), count=len(closed))

        return {"rolled_over": len(closed), "closed_budgets": closed}
