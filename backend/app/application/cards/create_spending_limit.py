"""Use case: Create a spending limit for a credit card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateSpendingLimitUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        card_id: uuid.UUID,
        *,
        limit_type: str,
        limit_amount: float,
        category_id: uuid.UUID | None = None,
        alert_threshold: int = 80,
        alert_enabled: bool = True,
        description: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        valid_types = {"daily", "weekly", "monthly", "category"}
        if limit_type not in valid_types:
            raise ValidationError(f"limit_type no valido: {limit_type}. Soportado: {', '.join(sorted(valid_types))}")

        if limit_amount <= 0:
            raise ValidationError("limit_amount debe ser mayor a 0")

        if limit_type == "category" and not category_id:
            raise ValidationError("category_id es requerido para limites de categoria")

        if not (1 <= alert_threshold <= 100):
            raise ValidationError("alert_threshold debe ser entre 1 y 100")

        limit = await self._repo.create_spending_limit(
            user_id,
            credit_card_id=card_id,
            limit_type=limit_type,
            limit_amount=limit_amount,
            spent_amount=0,
            category_id=category_id,
            alert_threshold=alert_threshold,
            alert_enabled=alert_enabled,
            description=description,
            is_active=True,
        )

        return {
            "id": str(limit.id),
            "credit_card_id": str(limit.credit_card_id),
            "limit_type": limit.limit_type,
            "limit_amount": str(limit.limit_amount),
            "spent_amount": str(limit.spent_amount),
            "category_id": str(limit.category_id) if limit.category_id else None,
            "alert_threshold": limit.alert_threshold,
            "alert_enabled": limit.alert_enabled,
            "description": limit.description,
            "is_active": limit.is_active,
            "created_at": limit.created_at.isoformat() if limit.created_at else None,
        }
