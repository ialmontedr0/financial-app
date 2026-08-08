"""Create a lent loan (préstamo otorgado) with a fixed term and installment."""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.lent_loans.amortization import (
    calculate_installment,
    generate_schedule,
)
from app.infrastructure.repositories.lent_loan_repository import LentLoanRepository
from app.middleware.error_handler import ValidationError
from app.utils.time import today_in

logger = structlog.get_logger()


class CreateLentLoanUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LentLoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        borrower_name: str,
        principal_amount: float,
        annual_interest_rate: float,
        term_months: int,
        payment_frequency: str = "monthly",
        currency_code: str = "DOP",
        account_id: str | None = None,
        start_date: str | None = None,
        is_collateralized: bool = False,
        notes: str | None = None,
    ) -> dict:
        if not borrower_name or not borrower_name.strip():
            raise ValidationError("El nombre del deudor es requerido")
        if principal_amount <= 0:
            raise ValidationError("El monto prestado debe ser mayor a 0")
        if annual_interest_rate < 0:
            raise ValidationError("La tasa de interés no puede ser negativa")
        if term_months <= 0 or term_months > 600:
            raise ValidationError("El plazo debe estar entre 1 y 600 meses")

        from app.application.lent_loans.serializers import serialize_lent_loan

        principal = Decimal(str(principal_amount))
        installment = calculate_installment(principal, annual_interest_rate, term_months)

        total_paid = installment * Decimal(term_months)
        total_interest = total_paid - principal
        if total_interest < 0:
            total_interest = Decimal("0")

        start = today_in()
        if start_date:
            start = date.fromisoformat(start_date)

        # first payment one month after start, final = month(term_months) after start
        first_payment_date = start + timedelta(days=30)
        month = start.month + term_months
        year = start.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        final_payment_date = date(year, month, min(start.day, monthrange(year, month)[1]))

        schedule = generate_schedule(
            principal_amount, annual_interest_rate, term_months, installment, start
        )

        loan = await self._repo.create(
            user_id=user_id,
            borrower_name=borrower_name.strip(),
            notes=notes,
            principal_amount=principal,
            annual_interest_rate=Decimal(str(annual_interest_rate)),
            term_months=term_months,
            payment_frequency=payment_frequency,
            currency_code=currency_code.upper(),
            monthly_payment=installment,
            current_balance=principal,
            total_received=Decimal("0"),
            total_interest_expected=total_interest,
            total_interest_received=Decimal("0"),
            start_date=start,
            first_payment_date=first_payment_date,
            next_payment_date=first_payment_date,
            final_payment_date=final_payment_date,
            status="active",
            is_collateralized=is_collateralized,
            account_id=uuid.UUID(account_id) if account_id else None,
        )

        await self._session.commit()

        logger.info("lent_loan_created", lent_loan_id=str(loan.id), term=term_months)
        return serialize_lent_loan(loan, schedule=schedule)