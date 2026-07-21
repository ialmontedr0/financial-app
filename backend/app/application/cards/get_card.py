"""Use case: Get credit card details."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetCardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        util = await self._repo.calculate_utilization(card_id, user_id)
        alerts = await self._repo.list_alerts(user_id, credit_card_id=card_id, is_dismissed=False)
        unread = sum(1 for a in alerts if not a.is_read)

        return {
            "id": str(card.id),
            "name": card.name,
            "account_id": str(card.account_id),
            "last_four_digits": card.last_four_digits,
            "card_network": card.card_network,
            "credit_limit": str(card.credit_limit) if card.credit_limit else None,
            "available_credit": str(card.available_credit) if card.available_credit is not None else None,
            "statement_day": card.statement_day,
            "payment_due_day": card.payment_due_day,
            "interest_rate": str(card.interest_rate) if card.interest_rate else None,
            "is_active": card.is_active,
            "include_in_totals": card.include_in_totals,
            "color": card.color,
            "icon": card.icon,
            "utilization": util,
            "unread_alerts": unread,
            "created_at": card.created_at.isoformat() if card.created_at else None,
            "updated_at": card.updated_at.isoformat() if card.updated_at else None,
        }
