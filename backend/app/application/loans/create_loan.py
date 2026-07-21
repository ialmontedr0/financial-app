"""Create a new loan."""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()

MONTHS_IN_YEAR = Decimal("12")
PERCENT_BASE = Decimal("100")


def calculate_monthly_payment(
    principal: Decimal, annual_rate: Decimal, term_months: int
) -> Decimal:
    """French amortization: M = P * [r(1+r)^n] / [(1+r)^n - 1]"""
    if annual_rate == 0:
        return (principal / Decimal(term_months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    r = annual_rate / PERCENT_BASE / MONTHS_IN_YEAR
    n = Decimal(term_months)
    factor = (1 + r) ** n
    payment = principal * (r * factor) / (factor - 1)
    return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_amortization_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
    monthly_payment: Decimal,
    start_date: date,
) -> list[dict]:
    """Generate full amortization schedule entries."""
    entries = []
    balance = principal
    r = annual_rate / PERCENT_BASE / MONTHS_IN_YEAR
    total_interest_to_date = Decimal("0")
    total_principal_to_date = Decimal("0")

    current_date = start_date + timedelta(days=30)

    for i in range(1, term_months + 1):
        interest = (balance * r).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        principal_portion = (monthly_payment - interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if i == term_months:
            principal_portion = balance
            payment_amount = principal_portion + interest
        else:
            payment_amount = monthly_payment

        balance = (balance - principal_portion).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if balance < 0:
            balance = Decimal("0")

        total_interest_to_date += interest
        total_principal_to_date += principal_portion

        # Calculate month/year for next entry
        month = current_date.month + 1
        year = current_date.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(current_date.day, monthrange(year, month)[1])
        current_date = date(year, month, day)

        entries.append(
            {
                "entry_number": i,
                "due_date": current_date,
                "payment_amount": payment_amount,
                "principal_portion": principal_portion,
                "interest_portion": interest,
                "balance_after": balance,
                "total_interest_to_date": total_interest_to_date,
                "total_principal_to_date": total_principal_to_date,
                "is_paid": False,
            }
        )

    return entries


class CreateLoanUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        name: str,
        principal_amount: float,
        annual_interest_rate: float,
        term_months: int,
        loan_type: str = "personal",
        interest_type: str = "fixed",
        payment_frequency: str = "monthly",
        account_id: str | None = None,
        lender_name: str | None = None,
        account_number: str | None = None,
        disbursement_date: str | None = None,
        grace_period_days: int = 0,
        early_payoff_allowed: bool = True,
        early_payoff_penalty_pct: float | None = None,
        penalty_rate_monthly: float | None = None,
        notes: str | None = None,
    ) -> dict:
        if not name or not name.strip():
            raise ValidationError("El nombre del préstamo es requerido")
        if principal_amount <= 0:
            raise ValidationError("El monto del préstamo debe ser mayor a 0")
        if annual_interest_rate < 0:
            raise ValidationError("La tasa de interés no puede ser negativa")
        if term_months <= 0:
            raise ValidationError("El plazo debe ser mayor a 0 meses")
        if term_months > 600:
            raise ValidationError("El plazo máximo es 600 meses (50 años)")

        principal = Decimal(str(principal_amount))
        rate = Decimal(str(annual_interest_rate))
        monthly_pmt = calculate_monthly_payment(principal, rate, term_months)
        total_interest = (monthly_pmt * Decimal(term_months) - principal).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        disbursement = date.today()  # noqa: DTZ011
        if disbursement_date:
            disbursement = date.fromisoformat(disbursement_date)

        first_payment = disbursement + timedelta(days=30)

        month = disbursement.month + term_months
        year = disbursement.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        final_payment = date(year, month, min(disbursement.day, 28))

        loan = await self._repo.create_loan(
            user_id=user_id,
            name=name.strip(),
            principal_amount=principal,
            current_balance=principal,
            annual_interest_rate=rate,
            interest_type=interest_type,
            term_months=term_months,
            payment_frequency=payment_frequency,
            monthly_payment=monthly_pmt,
            total_interest_expected=total_interest,
            loan_type=loan_type,
            account_id=uuid.UUID(account_id) if account_id else None,
            lender_name=lender_name,
            account_number=account_number,
            disbursement_date=disbursement,
            first_payment_date=first_payment,
            next_payment_date=first_payment,
            final_payment_date=final_payment,
            status="active",
            grace_period_days=grace_period_days,
            early_payoff_allowed=early_payoff_allowed,
            early_payoff_penalty_pct=Decimal(str(early_payoff_penalty_pct))
            if early_payoff_penalty_pct
            else None,
            penalty_rate_monthly=Decimal(str(penalty_rate_monthly))
            if penalty_rate_monthly
            else None,
            notes=notes,
        )

        # Generate amortization schedule
        schedule = generate_amortization_schedule(
            principal, rate, term_months, monthly_pmt, disbursement
        )
        await self._repo.create_amortization_entries(loan.id, schedule)

        logger.info("loan_created_with_amortization", loan_id=str(loan.id), entries=len(schedule))

        return {
            "id": str(loan.id),
            "name": loan.name,
            "loan_type": loan.loan_type,
            "principal_amount": float(loan.principal_amount),
            "current_balance": float(loan.current_balance),
            "annual_interest_rate": float(loan.annual_interest_rate),
            "interest_type": loan.interest_type,
            "term_months": loan.term_months,
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
            "status": loan.status,
            "lender_name": loan.lender_name,
            "account_number": loan.account_number,
            "notes": loan.notes,
            "amortization_entries_count": len(schedule),
            "created_at": loan.created_at.isoformat() if loan.created_at else None,
        }
