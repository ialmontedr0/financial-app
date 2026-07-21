"""Use case: List spending limits for a card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListSpendingLimitsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        limits = await self._repo.list_limits(user_id, card_id)

        items = []
        for lim in limits:
            updated = await self._repo.recalculate_limit_spent(lim.id, user_id) or lim
            pct = (float(updated.spent_amount) / float(updated.limit_amount) * 100) if float(updated.limit_amount) > 0 else 0
            items.append({
                "id": str(updated.id),
                "credit_card_id": str(updated.credit_card_id),
                "limit_type": updated.limit_type,
                "limit_amount": str(updated.limit_amount),
                "spent_amount": str(updated.spent_amount),
                "remaining": str(max(float(updated.limit_amount) - float(updated.spent_amount), 0)),
                "pct_used": round(pct, 1),
                "status": "exceeded" if pct > 100 else "warning" if pct >= updated.alert_threshold else "ok",
                "category_id": str(updated.category_id) if updated.category_id else None,
                "alert_threshold": updated.alert_threshold,
                "alert_enabled": updated.alert_enabled,
                "description": updated.description,
                "is_active": updated.is_active,
                "period_start": updated.period_start.isoformat() if updated.period_start else None,
                "period_end": updated.period_end.isoformat() if updated.period_end else None,
                "created_at": updated.created_at.isoformat() if updated.created_at else None,
            })

        return {"limits": items, "total": len(items)}
