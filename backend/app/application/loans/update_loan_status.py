"""Update loan status."""

from __future__ import annotations

import uuid
from datetime import date

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()

VALID_TRANSITIONS = {
    "pending": ["active", "cancelled"],
    "active": ["paid_off", "defaulted", "refinanced", "suspended"],
    "suspended": ["active", "defaulted"],
    "defaulted": ["active"],
}


class UpdateLoanStatusUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(self, user_id: uuid.UUID, loan_id: uuid.UUID, new_status: str) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")

        allowed = VALID_TRANSITIONS.get(loan.status, [])
        if new_status not in allowed:
            raise ValidationError(
                f"Transición no permitida: {loan.status} -> {new_status}. "
                f"Permitido: {', '.join(allowed)}"
            )

        updates: dict = {"status": new_status}
        if new_status == "paid_off":
            updates["paid_off_date"] = date.today()

        loan = await self._repo.update_loan(loan, **updates)

        return {
            "id": str(loan.id),
            "status": loan.status,
            "paid_off_date": loan.paid_off_date.isoformat() if loan.paid_off_date else None,
        }
