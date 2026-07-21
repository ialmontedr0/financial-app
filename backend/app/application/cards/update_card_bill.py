"""Use case: Update a credit card bill."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.card_repository import CardRepository

if TYPE_CHECKING:
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateCardBillUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CardRepository(session)

    async def execute(self, user_id: uuid.UUID, card_id: uuid.UUID, bill_id: uuid.UUID, *, changes: dict[str, Any]) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        card = await self._repo.get_card_by_id(card_id, user_id)
        if card is None:
            raise NotFoundError("CreditCard")

        allowed_fields = {"total_amount", "minimum_payment", "interest_charged", "payment_status", "notes"}
        filtered = {k: v for k, v in changes.items() if k in allowed_fields}

        if "payment_status" in filtered:
            valid_statuses = {"pending", "partial", "paid", "overdue", "waived"}
            if filtered["payment_status"] not in valid_statuses:
                raise ValidationError(f"payment_status no valido: {filtered['payment_status']}")

        if not filtered:
            return {"message": "No changes detected"}

        updated = await self._repo.update_bill(bill_id, user_id, **filtered)
        if updated is None:
            raise NotFoundError("CardBill")

        return {
            "id": str(updated.id),
            "credit_card_id": str(updated.credit_card_id),
            "statement_date": updated.statement_date.isoformat(),
            "due_date": updated.due_date.isoformat(),
            "total_amount": str(updated.total_amount),
            "minimum_payment": str(updated.minimum_payment) if updated.minimum_payment else None,
            "interest_charged": str(updated.interest_charged) if updated.interest_charged else None,
            "payment_status": updated.payment_status,
            "amount_paid": str(updated.amount_paid),
            "paid_at": updated.paid_at.isoformat() if updated.paid_at else None,
            "transaction_count": updated.transaction_count,
            "notes": updated.notes,
            "updated_at": updated.updated_at.isoformat() if updated.updated_at else None,
        }
