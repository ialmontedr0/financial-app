"""Use Case: escanea todos los presupuestos activos, recalcula gastos, crea alertas y notifica."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.budget_repository import BudgetRepository

from .rollover_expired_budgets import RolloverExpiredBudgetsUseCase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ScanBudgetsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BudgetRepository(session)

    async def execute(self) -> dict:
        from datetime import UTC, datetime

        from app.application.notifications.helpers import mirror_inapp_notifications

        user_ids = await self._repo.list_active_user_ids()
        today = datetime.now(UTC).date()
        users_scanned = 0
        notifications_created = 0

        for user_id in user_ids:
            # 1) Cerrar expirados + rollover (emite budget_closed)
            await RolloverExpiredBudgetsUseCase(self._session).execute(user_id)

            # 2) Recalcular gasto de cada presupuesto activo del periodo
            budgets = await self._repo.get_active_budgets_for_period(user_id, today, today)
            for budget in budgets:
                await self._repo.recalculate_spent(budget.id, user_id)

            # 3) Crear alertas nuevas y reflejarlas como notificaciones
            new_alerts = await self._repo.check_and_create_alerts(user_id)
            if new_alerts:
                items = [
                    {
                        "type": "budget_warning" if a.severity == "critical" else "budget_alert",
                        "title": a.title,
                        "body": a.message,
                        "data": {"alert_id": str(a.id), "budget_id": str(a.budget_id)},
                    }
                    for a in new_alerts
                ]
                notifications_created += await mirror_inapp_notifications(
                    self._session, user_id, items
                )

            users_scanned += 1

        logger.info("budgets_scanned", users=users_scanned, notifications=notifications_created)
        return {"users_scanned": users_scanned, "notifications_created": notifications_created}
