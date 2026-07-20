"""Repository for budget and budget alert persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select

from app.infrastructure.models.budget import BudgetModel
from app.infrastructure.models.budget_alert import BudgetAlertModel
from app.infrastructure.models.transaction import TransactionModel

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class BudgetRepository:
    """Repository for budget operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==============================================================
    # Budget CRUD
    # ==============================================================

    async def create_budget(self, user_id: uuid.UUID, **kwargs: object) -> BudgetModel:
        budget = BudgetModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(budget)
        await self._session.flush()
        logger.info(
            "budget_created",
            user_id=str(user_id),
            budget_id=str(budget.id),
            name=budget.name,
        )
        return budget

    async def get_budget_by_id(
        self, budget_id: uuid.UUID, user_id: uuid.UUID
    ) -> BudgetModel | None:
        stmt = select(BudgetModel).where(
            BudgetModel.id == budget_id,
            BudgetModel.user_id == user_id,
            BudgetModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_budgets(
        self,
        user_id: uuid.UUID,
        *,
        budget_type: str | None = None,
        is_active: bool | None = None,
        period: str | None = None,
    ) -> list[BudgetModel]:
        stmt = select(BudgetModel).where(
            BudgetModel.user_id == user_id,
            BudgetModel.deleted_at.is_(None),
        )
        if budget_type:
            stmt = stmt.where(BudgetModel.budget_type == budget_type)
        if is_active is not None:
            stmt = stmt.where(BudgetModel.is_active == is_active)
        if period:
            stmt = stmt.where(BudgetModel.period == period)
        stmt = stmt.order_by(BudgetModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_budgets_for_period(
        self, user_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[BudgetModel]:
        stmt = select(BudgetModel).where(
            BudgetModel.user_id == user_id,
            BudgetModel.deleted_at.is_(None),
            BudgetModel.is_active.is_(True),
            BudgetModel.start_date <= start_date,
            BudgetModel.end_date >= end_date,
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_budget(
        self, budget_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object
    ) -> BudgetModel | None:
        budget = await self.get_budget_by_id(budget_id, user_id)
        if budget is None:
            return None
        for key, value in kwargs.items():
            if hasattr(budget, key):
                setattr(budget, key, value)
        await self._session.flush()
        await self._session.refresh(budget)
        return budget

    async def delete_budget(self, budget_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        budget = await self.get_budget_by_id(budget_id, user_id)
        if budget is None:
            return False
        budget.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def recalculate_spent(
        self, budget_id: uuid.UUID, user_id: uuid.UUID
    ) -> BudgetModel | None:
        """Recalculate the spent amount for a budget from actual transactions."""
        budget = await self.get_budget_by_id(budget_id, user_id)
        if budget is None:
            return None

        stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            TransactionModel.user_id == user_id,
            TransactionModel.transaction_type == "expense",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= budget.start_date,
            TransactionModel.effective_date <= budget.end_date,
            TransactionModel.deleted_at.is_(None),
        )

        if budget.budget_type == "category" and budget.category_id:
            stmt = stmt.where(TransactionModel.category_id == budget.category_id)
        elif budget.budget_type == "account" and budget.account_id:
            stmt = stmt.where(TransactionModel.account_id == budget.account_id)

        result = await self._session.execute(stmt)
        spent = result.scalar_one()

        budget.spent = spent
        budget.remaining = budget.amount - spent
        await self._session.flush()
        await self._session.refresh(budget)
        return budget

    async def get_budget_summary(self, user_id: uuid.UUID) -> dict:
        """Get aggregated budget summary for the user."""
        budgets = await self.list_budgets(user_id, is_active=True)

        total_budget = sum(float(b.amount) for b in budgets)
        total_spent = sum(float(b.spent) for b in budgets)
        total_remaining = total_budget - total_spent

        over_budget_count = sum(1 for b in budgets if float(b.spent) > float(b.amount))
        near_limit_count = sum(
            1
            for b in budgets
            if float(b.amount) > 0
            and (float(b.spent) / float(b.amount) * 100) >= b.alert_threshold
            and float(b.spent) <= float(b.amount)
        )

        return {
            "total_budgets": len(budgets),
            "total_budget_amount": str(round(total_budget, 2)),
            "total_spent": str(round(total_spent, 2)),
            "total_remaining": str(round(total_remaining, 2)),
            "utilization_pct": str(
                round((total_spent / total_budget * 100) if total_budget > 0 else 0, 1)
            ),
            "over_budget_count": over_budget_count,
            "near_limit_count": near_limit_count,
        }

    async def get_monthly_spending(
        self, user_id: uuid.UUID, category_id: uuid.UUID | None = None
    ) -> list[dict]:
        """Get monthly spending totals for the last 3 months."""
        from datetime import date as date_type, timedelta

        today = date_type.today()  # noqa: DTZ011
        three_months_ago = today - timedelta(days=90)

        month_expr = func.date_trunc("month", TransactionModel.effective_date).label("month")
        stmt = select(
            month_expr,
            func.coalesce(func.sum(TransactionModel.amount), 0).label("total"),
        ).where(
            TransactionModel.user_id == user_id,
            TransactionModel.transaction_type == "expense",
            TransactionModel.status == "completed",
            TransactionModel.effective_date >= three_months_ago,
            TransactionModel.effective_date <= today,
            TransactionModel.deleted_at.is_(None),
        )
        if category_id:
            stmt = stmt.where(TransactionModel.category_id == category_id)
        stmt = stmt.group_by(month_expr)
        stmt = stmt.order_by(month_expr)

        result = await self._session.execute(stmt)
        return [{"month": str(row[0]), "total": str(row[1])} for row in result.all()]

    # ==============================================================
    # Budget Alerts CRUD
    # ==============================================================

    async def create_alert(self, user_id: uuid.UUID, **kwargs: object) -> BudgetAlertModel:
        alert = BudgetAlertModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(alert)
        await self._session.flush()
        logger.info(
            "budget_alert_created",
            user_id=str(user_id),
            alert_id=str(alert.id),
            alert_type=alert.alert_type,
        )
        return alert

    async def list_alerts(
        self,
        user_id: uuid.UUID,
        *,
        budget_id: uuid.UUID | None = None,
        is_read: bool | None = None,
        is_dismissed: bool | None = None,
        alert_type: str | None = None,
        severity: str | None = None,
    ) -> list[BudgetAlertModel]:
        stmt = select(BudgetAlertModel).where(
            BudgetAlertModel.user_id == user_id,
        )
        if budget_id:
            stmt = stmt.where(BudgetAlertModel.budget_id == budget_id)
        if is_read is not None:
            stmt = stmt.where(BudgetAlertModel.is_read == is_read)
        if is_dismissed is not None:
            stmt = stmt.where(BudgetAlertModel.is_dismissed == is_dismissed)
        if alert_type:
            stmt = stmt.where(BudgetAlertModel.alert_type == alert_type)
        if severity:
            stmt = stmt.where(BudgetAlertModel.severity == severity)
        stmt = stmt.order_by(BudgetAlertModel.triggered_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_alert_by_id(
        self, alert_id: uuid.UUID, user_id: uuid.UUID
    ) -> BudgetAlertModel | None:
        stmt = select(BudgetAlertModel).where(
            BudgetAlertModel.id == alert_id,
            BudgetAlertModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_alert_read(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        alert = await self.get_alert_by_id(alert_id, user_id)
        if alert is None:
            return False
        alert.is_read = True
        alert.read_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def mark_all_alerts_read(self, user_id: uuid.UUID) -> int:
        from datetime import UTC, datetime

        stmt = select(BudgetAlertModel).where(
            BudgetAlertModel.user_id == user_id,
            BudgetAlertModel.is_read.is_(False),
        )
        result = await self._session.execute(stmt)
        alerts = list(result.scalars().all())
        now = datetime.now(UTC)
        for alert in alerts:
            alert.is_read = True
            alert.read_at = now
        await self._session.flush()
        return len(alerts)

    async def dismiss_alert(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        alert = await self.get_alert_by_id(alert_id, user_id)
        if alert is None:
            return False
        alert.is_dismissed = True
        alert.dismissed_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def get_unread_alert_count(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(BudgetAlertModel).where(
            BudgetAlertModel.user_id == user_id,
            BudgetAlertModel.is_read.is_(False),
            BudgetAlertModel.is_dismissed.is_(False),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def check_and_create_alerts(self, user_id: uuid.UUID) -> list[BudgetAlertModel]:
        """Check all active budgets and create alerts where thresholds are met."""
        from datetime import date as date_type

        today = date_type.today()  # noqa: DTZ011
        budgets = await self.get_active_budgets_for_period(user_id, today, today)
        new_alerts: list[BudgetAlertModel] = []

        for budget in budgets:
            if not budget.alert_enabled or float(budget.amount) <= 0:
                continue

            pct = float(budget.spent) / float(budget.amount) * 100
            existing = await self.list_alerts(user_id, budget_id=budget.id)
            existing_types = {a.alert_type for a in existing}
            existing_thresholds = {a.threshold_percentage for a in existing if a.threshold_percentage}

            if pct >= 100 and "exceeded" not in existing_types:
                alert = await self.create_alert(
                    user_id,
                    budget_id=budget.id,
                    alert_type="exceeded",
                    severity="critical",
                    title=f"Presupuesto excedido: {budget.name}",
                    message=(
                        f"Has gastado ${float(budget.spent):,.2f} de un presupuesto "
                        f"de ${float(budget.amount):,.2f} ({pct:.1f}%). "
                        f"Excedido por ${float(budget.spent) - float(budget.amount):,.2f}."
                    ),
                    threshold_percentage=100,
                    current_amount=budget.spent,
                    budget_amount=budget.amount,
                )
                new_alerts.append(alert)
            elif pct >= budget.alert_threshold and budget.alert_threshold not in existing_thresholds:
                severity = "warning" if pct < 90 else "critical"
                alert = await self.create_alert(
                    user_id,
                    budget_id=budget.id,
                    alert_type="threshold",
                    severity=severity,
                    title=f"Alerta: {budget.name} al {pct:.0f}%",
                    message=(
                        f"Has gastado ${float(budget.spent):,.2f} de ${float(budget.amount):,.2f} "
                        f"({pct:.1f}%) en '{budget.name}'. "
                        f"Restante: ${float(budget.remaining):,.2f}."
                    ),
                    threshold_percentage=budget.alert_threshold,
                    current_amount=budget.spent,
                    budget_amount=budget.amount,
                )
                new_alerts.append(alert)

        return new_alerts
