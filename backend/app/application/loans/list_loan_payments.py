"""List payments for a loan."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class ListLoanPaymentsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        loan_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")

        payments = await self._repo.list_payments(loan_id, limit=limit, offset=offset)
        summary = await self._repo.get_payments_summary(loan_id)

        items = [
            {
                "id": str(p.id),
                "amount": float(p.amount),
                "principal_portion": float(p.principal_portion),
                "interest_portion": float(p.interest_portion),
                "penalty_portion": float(p.penalty_portion),
                "payment_date": p.payment_date.isoformat(),
                "payment_method": p.payment_method,
                "reference_number": p.reference_number,
                "status": p.status,
                "balance_after": float(p.balance_after),
                "is_extra_payment": p.is_extra_payment,
                "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ]

        return {
            "loan_id": str(loan_id),
            "payments": items,
            "total": len(items),
            "summary": summary,
        }
