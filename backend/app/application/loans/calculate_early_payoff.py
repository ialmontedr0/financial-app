"""Calculate early payoff amount for a loan."""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_UP, Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()

MONTHS_IN_YEAR = Decimal("12")
PERCENT_BASE = Decimal("100")


class CalculateEarlyPayoffUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        loan_id: uuid.UUID,
        payoff_date: str | None = None,
    ) -> dict:
        from datetime import date as _date

        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")
        if loan.status != "active":
            raise ValidationError("Solo préstamos activos pueden ser liquidados")
        if not loan.early_payoff_allowed:
            raise ValidationError("Este préstamo no permite liquidación anticipada")

        balance = Decimal(str(loan.current_balance))
        rate = Decimal(str(loan.annual_interest_rate))
        r = rate / PERCENT_BASE / MONTHS_IN_YEAR

        today = _date.today()
        if payoff_date:
            today = _date.fromisoformat(payoff_date)

        # Calculate remaining interest (simplified: sum of remaining months)
        remaining_months = 0
        if loan.next_payment_date:
            d1 = loan.next_payment_date
            remaining_months = (d1.year - today.year) * 12 + (d1.month - today.month)
            if remaining_months < 0:
                remaining_months = 0

        # Outstanding balance + pro-rata interest
        pro_rata_interest = (balance * r * Decimal(max(remaining_months, 1))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_payoff = balance + pro_rata_interest

        # Early payoff penalty
        penalty = Decimal("0")
        if loan.early_payoff_penalty_pct:
            penalty = (
                balance * Decimal(str(loan.early_payoff_penalty_pct)) / PERCENT_BASE
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_payoff += penalty

        # Interest saved
        total_expected_interest = Decimal(str(loan.total_interest_expected))
        interest_already_paid = Decimal(str(loan.total_interest_paid))
        remaining_interest_scheduled = total_expected_interest - interest_already_paid
        interest_saved = remaining_interest_scheduled - pro_rata_interest

        return {
            "loan_id": str(loan_id),
            "loan_name": loan.name,
            "current_balance": float(balance),
            "payoff_date": today.isoformat(),
            "remaining_months_scheduled": remaining_months,
            "outstanding_principal": float(balance),
            "pro_rata_interest": float(pro_rata_interest),
            "early_payoff_penalty": float(penalty),
            "total_payoff_amount": float(total_payoff),
            "interest_saved": float(max(interest_saved, Decimal("0"))),
            "monthly_payment_current": float(loan.monthly_payment),
            "total_paid_so_far": float(loan.total_paid),
        }
