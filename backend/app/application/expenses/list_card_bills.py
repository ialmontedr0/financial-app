"""Use case: List credit card bills for a specific card."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListCardBillsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, credit_card_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        card = await self._repo.get_credit_card_by_id(credit_card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        bills = await self._repo.list_card_bills(user_id, credit_card_id)

        items = [
            {
                "id": str(b.id),
                "credit_card_id": str(b.credit_card_id),
                "statement_date": b.statement_date.isoformat(),
                "due_date": b.due_date.isoformat(),
                "total_amount": str(b.total_amount),
                "minimum_payment": str(b.minimum_payment) if b.minimum_payment else None,
                "interest_charged": str(b.interest_charged) if b.interest_charged else None,
                "payment_status": b.payment_status,
                "amount_paid": str(b.amount_paid),
                "paid_at": b.paid_at.isoformat() if b.paid_at else None,
                "transaction_count": b.transaction_count,
                "notes": b.notes,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bills
        ]

        return {"bills": items, "total": len(items), "credit_card_id": str(credit_card_id)}
