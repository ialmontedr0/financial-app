"""Use case: List debit cards."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.debit_card_repository import DebitCardRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListDebitCardsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = DebitCardRepository(session)

    async def execute(self, user_id: uuid.UUID, account_id: uuid.UUID | None = None) -> dict:
        if account_id:
            cards = await self._repo.list_by_account(account_id, user_id)
        else:
            cards = await self._repo.list_by_user(user_id)

        items = [
            {
                "id": str(c.id),
                "account_id": str(c.account_id),
                "name": c.name,
                "last_four_digits": c.last_four_digits,
                "card_network": c.card_network,
                "is_active": c.is_active,
                "color": c.color,
                "notes": c.notes,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in cards
        ]

        return {"debit_cards": items, "total": len(items)}
