"""Get amortization schedule for a loan."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetAmortizationScheduleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(
        self, user_id: uuid.UUID, loan_id: uuid.UUID, paid_only: bool = False
    ) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")

        entries = await self._repo.list_amortization_entries(loan_id)
        if paid_only:
            entries = [e for e in entries if e.is_paid]

        items = [
            {
                "entry_number": e.entry_number,
                "due_date": e.due_date.isoformat(),
                "payment_amount": float(e.payment_amount),
                "principal_portion": float(e.principal_portion),
                "interest_portion": float(e.interest_portion),
                "balance_after": float(e.balance_after),
                "total_interest_to_date": float(e.total_interest_to_date),
                "total_principal_to_date": float(e.total_principal_to_date),
                "is_paid": e.is_paid,
            }
            for e in entries
        ]

        return {
            "loan_id": str(loan_id),
            "loan_name": loan.name,
            "total_entries": len(items),
            "entries": items,
        }
