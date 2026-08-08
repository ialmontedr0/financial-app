"""Get a single lent loan with its schedule and received payments."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from datetime import date

from app.application.lent_loans.amortization import generate_schedule
from app.application.lent_loans.serializers import serialize_lent_loan
from app.infrastructure.repositories.lent_loan_repository import LentLoanRepository
from app.middleware.error_handler import NotFoundError
from app.utils.time import today_in


class GetLentLoanUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LentLoanRepository(session)

    async def execute(self, user_id: uuid.UUID, lent_loan_id: uuid.UUID) -> dict:
        loan = await self._repo.get(lent_loan_id, user_id)
        if loan is None:
            raise NotFoundError("Préstamo otorgado")

        payments = await self._repo.list_payments(lent_loan_id)

        start = loan.start_date or loan.first_payment_date or today_in()

        schedule = generate_schedule(
            float(loan.principal_amount),
            float(loan.annual_interest_rate),
            loan.term_months,
            loan.monthly_payment,
            start,
        )

        schedule_payload = [
            {
                "entry_number": e["entry_number"],
                "due_date": e["due_date"].isoformat(),
                "amount": float(e["amount"]),
                "principal_portion": float(e["principal_portion"]),
                "interest_portion": float(e["interest_portion"]),
                "balance_after": float(e["balance_after"]),
            }
            for e in schedule
        ]

        return serialize_lent_loan(loan, payments=payments, schedule=schedule_payload)