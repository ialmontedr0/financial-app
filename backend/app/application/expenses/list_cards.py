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
                "account_id": str(c.account_id) if c.account_id else None,
                "last_four_digits": c.last_four_digits,
                "card_network": c.card_network,
                "currency_code": c.currency_code,
                "is_multicurrency": c.is_multicurrency,
                "secondary_currency_code": c.secondary_currency_code,
                "secondary_credit_limit": str(c.secondary_credit_limit) if c.secondary_credit_limit else None,
                "secondary_available_credit": str(c.secondary_available_credit) if c.secondary_available_credit else None,
                "credit_limit": str(c.credit_limit) if c.credit_limit else None,
                "available_credit": str(c.available_credit) if c.available_credit else None,
                "statement_day": c.statement_day,
                "payment_due_day": c.payment_due_day,
                "interest_rate": c.interest_rate,
                "is_active": c.is_active,
                "color": c.color,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cards
        ]

        return {"cards": items, "total": len(items)}
