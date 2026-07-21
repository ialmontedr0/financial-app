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
        new_alerts = await self._repo.check_and_create_alerts(user_id)
        unread = await self._repo.get_unread_alert_count(user_id)

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
