"""Use case: Get a debit card by ID."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.debit_card_repository import DebitCardRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetDebitCardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = DebitCardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        card = await self._repo.get_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("DebitCard")

        return {
            "id": str(card.id),
            "account_id": str(card.account_id),
            "name": card.name,
            "last_four_digits": card.last_four_digits,
            "card_network": card.card_network,
            "is_active": card.is_active,
            "color": card.color,
            "notes": card.notes,
            "created_at": card.created_at.isoformat() if card.created_at else None,
            "updated_at": card.updated_at.isoformat() if card.updated_at else None,
        }
