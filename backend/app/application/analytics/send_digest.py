"""Use Case: Envia una notificacion de un resumen financiero diario por usuario."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class SendDailyDigestUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def execute(self) -> dict:
        from datetime import UTC, datetime

        from sqlalchemy import func, select

        from app.infrastructure.models.transaction import TransactionModel
        from app.notifications.service import NotificationService

        since = datetime.now(UTC) - timedelta(days=7)
        user_ids = await self._user_repo.list_active_ids()
        service = NotificationService(self._session)
        sent = 0

        for user_id in user_ids:
            result = await self._session.execute(
                select(
                    TransactionModel.transaction_type,
                    func.sum(TransactionModel.amount),
                )
                .where(
                    TransactionModel.user_id == user_id,
                    TransactionModel.deleted_at.is_(None),
                    TransactionModel.created_at >= since,
                )
                .group_by(TransactionModel.transaction_type)
            )
            totals = {t: float(a) for t, a in result.all()}
            income = totals.get("income", 0.0)
            expense = totals.get("expense", 0.0)

            await service.send(
                user_id=user_id,
                type="system",
                title="Resumen semanal",
                body=f"Últimos 7 días: ingresos ${income:,.2f} · gastos ${expense:,.2f}.",
                data={"period": "weekly", "income": income, "expense": expense},
                channels=["email", "push"],
            )
            sent += 1

        logger.info("weekly_digest_sent", users=sent)
        return {"users_notified": sent}
