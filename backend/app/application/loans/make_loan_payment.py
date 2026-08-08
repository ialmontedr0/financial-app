"""Make a payment on a loan."""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.loan_repository import LoanRepository
from app.middleware.error_handler import NotFoundError, ValidationError
from app.utils.time import today_in

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
        loan = await self._repo.get_loan_for_update(loan_id, user_id)
        if not loan:
            raise NotFoundError("Loan")
        if loan.status not in ("active", "pending"):
            raise ValidationError(f"No se puede pagar un préstamo con estado '{loan.status}'")
        if amount <= 0:
            raise ValidationError("El monto del pago debe ser mayor a 0")

        pay_date = today_in()
        if payment_date:
            pay_date = date.fromisoformat(payment_date)

        pay_amount = Decimal(str(amount))
        balance = Decimal(str(loan.current_balance))
        monthly_rate = Decimal(str(loan.annual_interest_rate)) / PERCENT_BASE / MONTHS_IN_YEAR

        # Interés pro-rata diario: se cobra solo el interés acumulado desde el
        # último pago, no un mes completo por cada pago (evita doble interés
        # cuando hay varios pagos en el mismo mes).
        last_paid = (
            loan.last_payment_date
            or loan.disbursement_date
            or (loan.first_payment_date - timedelta(days=30) if loan.first_payment_date else None)
            or loan.created_at.date()
        )
        days = max((pay_date - last_paid).days, 0)
        daily_rate = monthly_rate / Decimal("30")
        interest = (balance * daily_rate * days).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
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

        pay_date = today_in()
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
            next_date = loan.next_payment_date
            month = next_date.month + 1
            year = next_date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(next_date.day, monthrange(year, month)[1])
            updates["next_payment_date"] = date(year, month, day)

        updates["last_payment_date"] = pay_date

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
