"""Record a payment received on a lent loan (préstamo otorgado)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.lent_loan_repository import LentLoanRepository
from app.middleware.error_handler import NotFoundError, ValidationError
from app.utils.time import today_in

logger = structlog.get_logger()


class RecordLentLoanPaymentUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LentLoanRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        lent_loan_id: uuid.UUID,
        amount: float,
        received_date: str | None = None,
        payment_method: str = "bank_transfer",
        reference_number: str | None = None,
        notes: str | None = None,
    ) -> dict:
        loan = await self._repo.get(lent_loan_id, user_id)
        if loan is None:
            raise NotFoundError("Préstamo otorgado")
        if amount <= 0:
            raise ValidationError("El monto recibido debe ser mayor a 0")
        if loan.current_balance <= 0:
            raise ValidationError("Este préstamo ya está pagado por completo")

        pmt_date = today_in()
        if received_date:
            pmt_date = date.fromisoformat(received_date)

        entered = Decimal(str(amount))
        if entered > loan.current_balance:
            raise ValidationError(
                "El monto recibido no puede superar el saldo pendiente"
            )

        # interest income = pending interest earned up to this payment's principal portion
        # simple split: everything above principal recovered that period is interest.
        # We approximate: interest_portion = amount * rate/100/12 (period interest share),
        # principal_portion = amount - interest_portion (capped at balance).
        if loan.payment_frequency == "single_payment":
            # interest accrues over the whole term; pay expected interest first
            interest_share = entered - loan.principal_amount
            principal_share = entered - interest_share
            if principal_share < 0:
                principal_share = entered
                interest_share = Decimal("0")
        else:
            period_rate = (
                Decimal(str(loan.annual_interest_rate)) / Decimal("100") / Decimal("12")
            )
            interest_share = (entered * period_rate).quantize(Decimal("0.01"))
            principal_share = entered - interest_share
            if principal_share < 0:
                principal_share = entered
                interest_share = Decimal("0")
        if principal_share > loan.current_balance:
            principal_share = loan.current_balance
            interest_share = entered - principal_share

        await self._repo.add_payment(
            lent_loan_id=lent_loan_id,
            user_id=user_id,
            amount=entered,
            principal_portion=principal_share,
            interest_portion=interest_share,
            received_date=pmt_date,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
        )

        new_balance = loan.current_balance - principal_share
        new_received = loan.total_received + entered
        # New paid-off state
        is_paid_off = new_balance <= 0

        await self._repo.update(
            loan,
            current_balance=max(new_balance, Decimal("0")),
            total_received=new_received,
            total_interest_received=loan.total_interest_received + interest_share,
            next_payment_date=None if is_paid_off else loan.next_payment_date,
            status="paid_off" if is_paid_off else loan.status,
            paid_off_date=pmt_date if is_paid_off else None,
        )

        # El cobro del deudor se acredita a la cuenta origen del préstamo.
        if loan.account_id:
            from app.infrastructure.repositories.transaction_repository import (
                TransactionRepository,
            )

            await TransactionRepository(self._session).update_account_balance(
                loan.account_id, entered, "add"
            )

        await self._session.commit()

        logger.info(
            "lent_loan_payment_recorded",
            lent_loan_id=str(lent_loan_id),
            amount=float(entered),
        )
        from app.application.lent_loans.serializers import serialize_lent_loan

        return serialize_lent_loan(loan)
