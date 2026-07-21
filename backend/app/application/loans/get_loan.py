"""Get loan detail."""

from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetLoanUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(self, user_id: uuid.UUID, loan_id: uuid.UUID) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")

        payments_summary = await self._repo.get_payments_summary(loan_id)
        upcoming = []
        if loan.status == "active" and loan.next_payment_date:
            from datetime import date as _date

            days_until = (loan.next_payment_date - _date.today()).days  # noqa: DTZ011
            upcoming.append(
                {
                    "next_payment_date": loan.next_payment_date.isoformat(),
                    "monthly_payment": float(loan.monthly_payment),
                    "days_until_payment": days_until,
                }
            )

        progress_pct = 0.0
        if loan.principal_amount > 0:
            paid_principal = float(loan.principal_amount) - float(loan.current_balance)
            progress_pct = round(paid_principal / float(loan.principal_amount) * 100, 2)

        return {
            "id": str(loan.id),
            "name": loan.name,
            "description": loan.description,
            "loan_type": loan.loan_type,
            "lender_name": loan.lender_name,
            "account_number": loan.account_number,
            "principal_amount": float(loan.principal_amount),
            "current_balance": float(loan.current_balance),
            "annual_interest_rate": float(loan.annual_interest_rate),
            "interest_type": loan.interest_type,
            "term_months": loan.term_months,
            "payment_frequency": loan.payment_frequency,
            "monthly_payment": float(loan.monthly_payment),
            "total_paid": float(loan.total_paid),
            "total_interest_paid": float(loan.total_interest_paid),
            "total_interest_expected": float(loan.total_interest_expected),
            "disbursement_date": loan.disbursement_date.isoformat()
            if loan.disbursement_date
            else None,
            "first_payment_date": loan.first_payment_date.isoformat()
            if loan.first_payment_date
            else None,
            "next_payment_date": loan.next_payment_date.isoformat()
            if loan.next_payment_date
            else None,
            "final_payment_date": loan.final_payment_date.isoformat()
            if loan.final_payment_date
            else None,
            "paid_off_date": loan.paid_off_date.isoformat() if loan.paid_off_date else None,
            "status": loan.status,
            "grace_period_days": loan.grace_period_days,
            "early_payoff_allowed": loan.early_payoff_allowed,
            "early_payoff_penalty_pct": float(loan.early_payoff_penalty_pct)
            if loan.early_payoff_penalty_pct
            else None,
            "penalty_rate_monthly": float(loan.penalty_rate_monthly)
            if loan.penalty_rate_monthly
            else None,
            "progress_pct": progress_pct,
            "payments_summary": payments_summary,
            "upcoming_payment": upcoming[0] if upcoming else None,
            "notes": loan.notes,
            "created_at": loan.created_at.isoformat() if loan.created_at else None,
        }
