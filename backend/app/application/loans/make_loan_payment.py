"""Make a payment on a loan."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()

PERCENT_BASE = Decimal("100")
MONTHS_IN_YEAR = Decimal("12")


class MakeLoanPaymentUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        loan_id: uuid.UUID,
        amount: float,
        payment_date: str | None = None,
        payment_method: str = "bank_transfer",
        reference_number: str | None = None,
        is_extra_payment: bool = False,
        notes: str | None = None,
    ) -> dict:
        loan = await self._repo.get_loan(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")
        if loan.status not in ("active", "pending"):
            raise ValidationError(f"No se puede pagar un préstamo con estado '{loan.status}'")
        if amount <= 0:
            raise ValidationError("El monto del pago debe ser mayor a 0")

        pay_amount = Decimal(str(amount))
        balance = Decimal(str(loan.current_balance))
        r = Decimal(str(loan.annual_interest_rate)) / PERCENT_BASE / MONTHS_IN_YEAR

        # Calculate portions
        interest = (balance * r).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if pay_amount <= interest:
            raise ValidationError(
                f"El monto del pago ({pay_amount}) es menor que el interés del mes ({interest}). "
                f"Mínimo: {interest}"
            )

        principal_portion = (pay_amount - interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if principal_portion > balance:
            principal_portion = balance
            pay_amount = principal_portion + interest

        new_balance = (balance - principal_portion).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if new_balance < 0:
            new_balance = Decimal("0")

        pay_date = date.today()
        if payment_date:
            pay_date = date.fromisoformat(payment_date)

        payment = await self._repo.create_payment(
            loan_id=loan_id,
            amount=pay_amount,
            principal_portion=principal_portion,
            interest_portion=interest,
            penalty_portion=Decimal("0"),
            payment_date=pay_date,
            payment_method=payment_method,
            reference_number=reference_number,
            status="completed",
            balance_after=new_balance,
            is_extra_payment=is_extra_payment,
            notes=notes,
        )

        # Update loan
        new_total_paid = Decimal(str(loan.total_paid)) + pay_amount
        new_total_interest = Decimal(str(loan.total_interest_paid)) + interest

        updates: dict = {
            "current_balance": new_balance,
            "total_paid": new_total_paid,
            "total_interest_paid": new_total_interest,
        }

        if new_balance == 0:
            updates["status"] = "paid_off"
            updates["paid_off_date"] = pay_date

        # Calculate next payment date
        if new_balance > 0 and loan.next_payment_date:
            from datetime import timedelta

            next = loan.next_payment_date
            month = next.month + 1
            year = next.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            from calendar import monthrange

            day = min(next.day, monthrange(year, month)[1])
            updates["next_payment_date"] = date(year, month, day)

        loan = await self._repo.update_loan(loan, **updates)

        return {
            "payment_id": str(payment.id),
            "loan_id": str(loan_id),
            "amount": float(payment.amount),
            "principal_portion": float(payment.principal_portion),
            "interest_portion": float(payment.interest_portion),
            "penalty_portion": float(payment.penalty_portion),
            "payment_date": payment.payment_date.isoformat(),
            "payment_method": payment.payment_method,
            "balance_after": float(new_balance),
            "is_extra_payment": is_extra_payment,
            "loan_status": loan.status,
            "current_balance": float(loan.current_balance),
            "total_paid": float(loan.total_paid),
            "total_interest_paid": float(loan.total_interest_paid),
        }
