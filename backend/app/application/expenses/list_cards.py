"""Use case: List credit cards."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListCardsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        cards = await self._repo.list_credit_cards(user_id)

        items = [
            {
                "id": str(c.id),
                "name": c.name,
                "account_id": str(c.account_id),
                "last_four_digits": c.last_four_digits,
                "card_network": c.card_network,
                "credit_limit": str(c.credit_limit) if c.credit_limit else None,
                "available_credit": str(c.available_credit) if c.available_credit else None,
                "statement_day": c.statement_day,
                "payment_due_day": c.payment_due_day,
                "interest_rate": str(c.interest_rate) if c.interest_rate else None,
                "is_active": c.is_active,
                "color": c.color,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cards
        ]

        return {"cards": items, "total": len(items)}
