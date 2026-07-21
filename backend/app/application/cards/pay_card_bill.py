"""Use case: Record a payment on a credit card bill."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class PayCardBillUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        card_id: uuid.UUID,
        bill_id: uuid.UUID,
        *,
        amount: float,
        payment_method: str = "manual",
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        if amount <= 0:
            raise ValidationError("amount debe ser mayor a 0")

        bill = await self._repo.pay_bill(bill_id, user_id, amount, payment_method)
        if bill is None:
            raise NotFoundError("CardBill")

        return {
            "id": str(bill.id),
            "credit_card_id": str(bill.credit_card_id),
            "statement_date": bill.statement_date.isoformat(),
            "due_date": bill.due_date.isoformat(),
            "total_amount": str(bill.total_amount),
            "amount_paid": str(bill.amount_paid),
            "payment_status": bill.payment_status,
            "paid_at": bill.paid_at.isoformat() if bill.paid_at else None,
            "payment_amount": str(amount),
            "payment_method": payment_method,
        }
