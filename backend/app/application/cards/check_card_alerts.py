"""Use case: Check all cards and generate alerts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CheckCardAlertsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        from app.application.notifications.helpers import mirror_inapp_notifications

        new_alerts = await self._repo.check_and_create_alerts(user_id)
        unread = await self._repo.get_unread_alert_count(user_id)

        if new_alerts:
            await mirror_inapp_notifications(
                self._session,
                user_id,
                [
                    {
                        "type": self._notification_type(a.alert_type),
                        "title": a.title,
                        "body": a.message,
                        "data": {"alert_id": str(a.id), "credit_card_id": str(a.credit_card_id)},
                    }
                    for a in new_alerts
                ],
            )

        return {
            "new_alerts": len(new_alerts),
            "unread_alerts": unread,
            "alerts_created": [
                {
                    "id": str(a.id),
                    "alert_type": a.alert_type,
                    "severity": a.severity,
                    "title": a.title,
                }
                for a in new_alerts
            ],
        }

    @staticmethod
    def _notification_type(alert_type: str) -> str:
        mapping = {
            "high_utilization": "budget_warning",
            "limit_approaching": "budget_warning",
            "due_date_approaching": "bill_due",
            "payment_overdue": "payment_due",
        }
        return mapping.get(alert_type, "security_alert")
