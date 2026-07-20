"""Use case: Create a credit card bill/statement."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from decimal import Decimal  # noqa: F401

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateCardBillUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        credit_card_id: uuid.UUID,
        statement_date: date,
        due_date: date,
        total_amount: float,
        minimum_payment: float | None = None,
        interest_charged: float | None = None,
        notes: str | None = None,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        card = await self._repo.get_credit_card_by_id(credit_card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        if due_date <= statement_date:
            raise ValidationError("due_date debe ser posterior a statement_date")
        if total_amount < 0:
            raise ValidationError("total_amount no puede ser negativo")

        bill = await self._repo.create_card_bill(
            user_id,
            credit_card_id=credit_card_id,
            statement_date=statement_date,
            due_date=due_date,
            total_amount=total_amount,
            minimum_payment=minimum_payment,
            interest_charged=interest_charged,
            notes=notes,
        )

        return {
            "id": str(bill.id),
            "credit_card_id": str(bill.credit_card_id),
            "statement_date": bill.statement_date.isoformat(),
            "due_date": bill.due_date.isoformat(),
            "total_amount": str(bill.total_amount),
            "minimum_payment": str(bill.minimum_payment) if bill.minimum_payment else None,
            "interest_charged": str(bill.interest_charged) if bill.interest_charged else None,
            "payment_status": bill.payment_status,
            "amount_paid": str(bill.amount_paid),
            "transaction_count": bill.transaction_count,
            "notes": bill.notes,
            "created_at": bill.created_at.isoformat() if bill.created_at else None,
        }
