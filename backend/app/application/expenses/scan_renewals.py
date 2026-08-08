"""Use Case: Recuerda al usuario las renovaciones de suscripciones en los proximos dias."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

REMINDER_HORIZON_DAYS = 7


class ScanSubscriptionRenewalsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self) -> dict:
        from datetime import UTC, datetime

        from sqlalchemy import select

        from app.infrastructure.models.subscription import SubscriptionModel
        from app.infrastructure.repositories.notification_repository import NotificationRepository
        from app.notifications.service import NotificationService

        today = datetime.now(UTC).date()
        horizon = today + timedelta(days=REMINDER_HORIZON_DAYS)

        result = await self._session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.status == "active",
                SubscriptionModel.deleted_at.is_(None),
                SubscriptionModel.next_billing_date.is_not(None),
                SubscriptionModel.next_billing_date >= today,
                SubscriptionModel.next_billing_date <= horizon,
            )
        )
        subscriptions = result.scalars().all()

        repo = NotificationRepository(self._session)
        service = NotificationService(self._session)
        emitted = 0

        for sub in subscriptions:
            already_this_sub = await repo.exists_with_data(
                sub.user_id, "bill_due", "subscription_id", str(sub.id)
            )
            already_this_period = await repo.exists_with_data(
                sub.user_id, "bill_due", "due_date", sub.next_billing_date.isoformat()
            )
            # Aviso una sola vez por suscripcion y por periodo (evita duplicados)
            if already_this_sub and already_this_period:
                continue
            days_left = (sub.next_billing_date - today).days
            await service.send(
                user_id=sub.user_id,
                type="bill_due",
                title=f"Renovacion proxima: {sub.name}",
                body=(
                    f"'{sub.name}' se renovara el {sub.next_billing_date.isoformat()} "
                    f"({days_left} dia{'s' if days_left != 1 else ''}). "
                    f"Monto: ${float(sub.amount):,.2f} {sub.currency_code}."
                ),
                data={
                    "subscription_id": str(sub.id),
                    "amount": str(sub.amount),
                    "currency_code": sub.currency_code,
                    "due_date": sub.next_billing_date.isoformat(),
                    "link": "/expenses/subscriptions",
                },
            )
            emitted += 1

        logger.info(
            "subscription_renewals_scanned", subscriptions=len(subscriptions), emitted=emitted
        )
        return {"subscriptions_found": len(subscriptions), "notified": emitted}
