"""Use case: Update a spending limit."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateSpendingLimitUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID, limit_id: uuid.UUID, *, changes: dict[str, Any]) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        allowed_fields = {"limit_amount", "alert_threshold", "alert_enabled", "description", "is_active"}
        filtered = {k: v for k, v in changes.items() if k in allowed_fields}

        if "limit_amount" in filtered:
            if filtered["limit_amount"] <= 0:
                raise ValidationError("limit_amount debe ser mayor a 0")

        if "alert_threshold" in filtered:
            if not (1 <= filtered["alert_threshold"] <= 100):
                raise ValidationError("alert_threshold debe ser entre 1 y 100")

        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_limit(limit_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("SpendingLimit")

        pct = (float(updated.spent_amount) / float(updated.limit_amount) * 100) if float(updated.limit_amount) > 0 else 0

        return {
            "id": str(updated.id),
            "credit_card_id": str(updated.credit_card_id),
            "limit_type": updated.limit_type,
            "limit_amount": str(updated.limit_amount),
            "spent_amount": str(updated.spent_amount),
            "pct_used": round(pct, 1),
            "category_id": str(updated.category_id) if updated.category_id else None,
            "alert_threshold": updated.alert_threshold,
            "alert_enabled": updated.alert_enabled,
            "description": updated.description,
            "is_active": updated.is_active,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
