"""Use case: Create a credit card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateCardUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, **kwargs: object) -> dict:
        card = await self._repo.create_credit_card(user_id, **kwargs)  # type: ignore[arg-type]

        return {
            "id": str(card.id),
            "name": card.name,
            "account_id": str(card.account_id) if card.account_id else None,
            "last_four_digits": card.last_four_digits,
            "card_network": card.card_network,
            "currency_code": card.currency_code,
            "is_multicurrency": card.is_multicurrency,
            "secondary_currency_code": card.secondary_currency_code,
            "secondary_credit_limit": str(card.secondary_credit_limit) if card.secondary_credit_limit else None,
            "secondary_available_credit": str(card.secondary_available_credit) if card.secondary_available_credit else None,
            "credit_limit": str(card.credit_limit) if card.credit_limit else None,
            "available_credit": str(card.available_credit) if card.available_credit else None,
            "statement_day": card.statement_day,
            "payment_due_day": card.payment_due_day,
            "interest_rate": str(card.interest_rate) if card.interest_rate else None,
            "is_active": card.is_active,
            "color": card.color,
            "created_at": card.created_at.isoformat() if card.created_at else None,
        }
