"""Update loan."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()

ALLOWED_FIELDS = {
    "name",
    "description",
    "lender_name",
    "account_number",
    "notes",
    "grace_period_days",
    "early_payoff_allowed",
    "early_payoff_penalty_pct",
    "penalty_rate_monthly",
}


class UpdateLoanUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(self, user_id: uuid.UUID, loan_id: uuid.UUID, body: dict) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")

        updates = {k: v for k, v in body.items() if k in ALLOWED_FIELDS and v is not None}
        if not updates:
            raise ValidationError("No hay campos para actualizar")

        if "name" in updates and not updates["name"].strip():
            raise ValidationError("El nombre no puede estar vacío")

        loan = await self._repo.update_loan(loan, **updates)

        return {
            "id": str(loan.id),
            "name": loan.name,
            "description": loan.description,
            "lender_name": loan.lender_name,
            "account_number": loan.account_number,
            "grace_period_days": loan.grace_period_days,
            "early_payoff_allowed": loan.early_payoff_allowed,
            "early_payoff_penalty_pct": float(loan.early_payoff_penalty_pct)
            if loan.early_payoff_penalty_pct
            else None,
            "penalty_rate_monthly": float(loan.penalty_rate_monthly)
            if loan.penalty_rate_monthly
            else None,
            "notes": loan.notes,
            "status": loan.status,
        }
