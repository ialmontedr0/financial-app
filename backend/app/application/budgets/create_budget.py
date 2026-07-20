"""Use case: Create a budget."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateBudgetUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        name: str,
        amount: float,
        budget_type: str = "total",
        period: str = "monthly",
        start_date: date | None = None,
        end_date: date | None = None,
        category_id: uuid.UUID | None = None,
        account_id: uuid.UUID | None = None,
        alert_threshold: int = 80,
        alert_enabled: bool = True,
        auto_adjust: bool = False,
        rollover: bool = False,
        strategy: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
    ) -> dict:
        from datetime import date as date_type, timedelta

        from app.middleware.error_handler import ValidationError

        if not name or not name.strip():
            raise ValidationError("Budget name es requerido")
        if amount <= 0:
            raise ValidationError("amount debe ser mayor a 0")

        valid_types = {"total", "category", "account"}
        if budget_type not in valid_types:
            raise ValidationError(f"budget_type no valido: {budget_type}. Soportado: {', '.join(sorted(valid_types))}")

        valid_periods = {"weekly", "biweekly", "monthly", "quarterly", "yearly"}
        if period not in valid_periods:
            raise ValidationError(f"period no valido: {period}. Soportado: {', '.join(sorted(valid_periods))}")

        if not (1 <= alert_threshold <= 100):
            raise ValidationError("alert_threshold debe ser entre 1 y 100")

        if budget_type == "category" and not category_id:
            raise ValidationError("category_id es requerido para presupuestos de categoria")
        if budget_type == "account" and not account_id:
            raise ValidationError("account_id es requerido para presupuestos de cuenta")

        today = date_type.today()  # noqa: DTZ011
        if start_date is None:
            start_date = today.replace(day=1)
        if end_date is None:
            if period == "weekly":
                end_date = start_date + timedelta(days=6)
            elif period == "biweekly":
                end_date = start_date + timedelta(days=13)
            elif period == "monthly":
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
            elif period == "quarterly":
                quarter_month = ((start_date.month - 1) // 3 + 1) * 3
                if quarter_month >= 12:
                    end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=quarter_month + 1, day=1) - timedelta(days=1)
            elif period == "yearly":
                end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)

        valid_strategies = {None, "zero_based", "50_30_20", "envelope", "custom"}
        if strategy not in valid_strategies:
            raise ValidationError(f"strategy no valido: {strategy}")

        budget = await self._repo.create_budget(
            user_id,
            name=name.strip(),
            description=description,
            budget_type=budget_type,
            amount=amount,
            spent=0,
            remaining=amount,
            period=period,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            account_id=account_id,
            alert_threshold=alert_threshold,
            alert_enabled=alert_enabled,
            auto_adjust=auto_adjust,
            rollover=rollover,
            strategy=strategy,
            is_active=True,
            icon=icon,
            color=color,
        )

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
            "is_active": budget.is_active,
            "icon": budget.icon,
            "color": budget.color,
            "created_at": budget.created_at.isoformat() if budget.created_at else None,
        }
