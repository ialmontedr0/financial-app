"""Get amortization summary statistics."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetAmortizationSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(self, user_id: uuid.UUID, loan_id: uuid.UUID) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")

        entries = await self._repo.list_amortization_entries(loan_id)
        paid_count = sum(1 for e in entries if e.is_paid)
        total_interest = sum(e.interest_portion for e in entries) if entries else 0
        total_principal = sum(e.principal_portion for e in entries) if entries else 0

        return {
            "loan_id": str(loan_id),
            "total_entries": len(entries),
            "entries_paid": paid_count,
            "entries_remaining": len(entries) - paid_count,
            "progress_pct": round(paid_count / len(entries) * 100, 2) if entries else 0,
            "total_interest_scheduled": float(total_interest),
            "total_principal_scheduled": float(total_principal),
            "monthly_payment": float(loan.monthly_payment),
            "current_balance": float(loan.current_balance),
        }
