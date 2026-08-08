"""Create a lent loan (préstamo otorgado) with a fixed term and installment."""

from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import date
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.lent_loans.amortization import (
    calculate_installment,
    calculate_single_payment,
    generate_schedule,
    months_between,
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
        term_months: int | None = None,
        payment_frequency: str = "monthly",
        currency_code: str = "DOP",
        account_id: str | None = None,
        start_date: str | None = None,
        is_collateralized: bool = False,
        notes: str | None = None,
        single_payment_date: str | None = None,
    ) -> dict:
        if not borrower_name or not borrower_name.strip():
            raise ValidationError("El nombre del deudor es requerido")
        if principal_amount <= 0:
            raise ValidationError("El monto prestado debe ser mayor a 0")
        if annual_interest_rate < 0:
            raise ValidationError("La tasa de interés no puede ser negativa")

        is_single = payment_frequency == "single_payment"

        acct_uuid = uuid.UUID(account_id) if account_id else None
        if acct_uuid:
            from app.infrastructure.repositories.account_repository import AccountRepository

            account = await AccountRepository(self._session).get_by_id(acct_uuid, user_id)
            if account is None:
                raise ValidationError("La cuenta de origen no existe")

        if is_single:
            if not single_payment_date:
                raise ValidationError(
                    "Para el pago único se requiere el mes y año del pago"
                )
            try:
                due = date.fromisoformat(single_payment_date)
            except ValueError:
                raise ValidationError(
                    "La fecha del pago único no es válida"
                ) from None
            start = today_in()
            if start_date:
                start = date.fromisoformat(start_date)
            if due <= start:
                raise ValidationError(
                    "La fecha del pago único debe ser posterior a la fecha de inicio"
                )
            term_months = months_between(start, due)
        else:
            if term_months is None:
                raise ValidationError("El plazo es requerido")
            if term_months <= 0 or term_months > 600:
                raise ValidationError("El plazo debe estar entre 1 y 600 meses")

        from app.application.lent_loans.serializers import serialize_lent_loan

        principal = Decimal(str(principal_amount))
        if is_single:
            installment = calculate_single_payment(
                principal, annual_interest_rate, term_months
            )
        else:
            installment = calculate_installment(
                principal, annual_interest_rate, term_months
            )

        total_paid = installment if is_single else installment * Decimal(term_months)
        total_interest = total_paid - principal
        if total_interest < 0:
            total_interest = Decimal("0")

        if not is_single:
            start = today_in()
            if start_date:
                start = date.fromisoformat(start_date)

            # first payment one month after start, final = month(term_months) after start
            month = start.month + term_months
            year = start.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            final_payment_date = date(
                year, month, min(start.day, monthrange(year, month)[1])
            )
            due = final_payment_date

        schedule = generate_schedule(
            principal_amount,
            annual_interest_rate,
            term_months,
            installment,
            start,
            payment_frequency=payment_frequency,
            single_payment_date=due if is_single else None,
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
            first_payment_date=due,
            next_payment_date=due,
            final_payment_date=due,
            status="active",
            is_collateralized=is_collateralized,
            account_id=acct_uuid,
            single_payment_date=due if is_single else None,
        )

        # El desembolso sale de la cuenta origen seleccionada.
        if acct_uuid:
            from app.infrastructure.repositories.transaction_repository import (
                TransactionRepository,
            )

            await TransactionRepository(self._session).update_account_balance(
                acct_uuid, principal, "subtract"
            )

        await self._session.commit()

        logger.info("lent_loan_created", lent_loan_id=str(loan.id), term=term_months)
        return serialize_lent_loan(loan, schedule=schedule)
