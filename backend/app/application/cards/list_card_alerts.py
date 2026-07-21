"""Use case: List card alerts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListCardAlertsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        credit_card_id: uuid.UUID | None = None,
        is_read: bool | None = None,
        alert_type: str | None = None,
        severity: str | None = None,
    ) -> dict:
        alerts = await self._repo.list_alerts(
            user_id,
            credit_card_id=credit_card_id,
            is_read=is_read,
            alert_type=alert_type,
            severity=severity,
        )

        items = [
            {
                "id": str(a.id),
                "credit_card_id": str(a.credit_card_id),
                "credit_card_bill_id": str(a.credit_card_bill_id) if a.credit_card_bill_id else None,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "threshold_percentage": a.threshold_percentage,
                "current_amount": str(a.current_amount) if a.current_amount else None,
                "limit_amount": str(a.limit_amount) if a.limit_amount else None,
                "is_read": a.is_read,
                "is_dismissed": a.is_dismissed,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            }
            for a in alerts
        ]

        return {"alerts": items, "total": len(items)}
