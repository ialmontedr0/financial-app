"""Use case: Auto-generate a statement from transactions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GenerateStatementUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        bill = await self._repo.generate_statement(card_id, user_id)
        if bill is None:
            return {"message": "No transactions found for statement generation"}

        return {
            "id": str(bill.id),
            "credit_card_id": str(bill.credit_card_id),
            "statement_date": bill.statement_date.isoformat(),
            "due_date": bill.due_date.isoformat(),
            "total_amount": str(bill.total_amount),
            "minimum_payment": str(bill.minimum_payment) if bill.minimum_payment else None,
            "interest_charged": str(bill.interest_charged) if bill.interest_charged else None,
            "transaction_count": bill.transaction_count,
            "payment_status": bill.payment_status,
        }
