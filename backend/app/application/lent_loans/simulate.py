"""Simulate a lent loan (préstamo otorgado) — stateless calculator."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.application.lent_loans.amortization import (
    calculate_installment,
    calculate_single_payment,
    compute_schedule_totals,
    generate_schedule,
    months_between,
)
from app.middleware.error_handler import ValidationError
from app.utils.time import today_in


class SimulateLentLoanUseCase:
    """Compute installments, totals and schedule without saving anything."""

    def __init__(self, session=None) -> None:
        self._session = session

    async def execute(
        self,
        principal_amount: float,
        annual_interest_rate: float,
        term_months: int | None = None,
        start_date: str | None = None,
        payment_frequency: str = "monthly",
        single_payment_date: str | None = None,
    ) -> dict:
        if principal_amount <= 0:
            raise ValidationError("El monto prestado debe ser mayor a 0")
        if annual_interest_rate < 0:
            raise ValidationError("La tasa de interés no puede ser negativa")

        is_single = payment_frequency == "single_payment"

        start = today_in()
        if start_date:
            start = date.fromisoformat(start_date)

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

        principal = Decimal(str(principal_amount))
        if is_single:
            installment = calculate_single_payment(
                principal, annual_interest_rate, term_months
            )
        else:
            installment = calculate_installment(
                principal, annual_interest_rate, term_months
            )

        schedule = generate_schedule(
            principal_amount,
            annual_interest_rate,
            term_months,
            installment,
            start,
            payment_frequency=payment_frequency,
            single_payment_date=due if is_single else None,
        )

        if is_single:
            totals = {
                "total_paid": installment,
                "total_interest": max(installment - principal, Decimal("0")),
                "interest_to_principal_ratio": round(
                    float(max(installment - principal, Decimal("0")) / principal) * 100, 2
                )
                if principal > 0
                else 0,
            }
        else:
            totals = compute_schedule_totals(principal, term_months, installment)

        return {
            "principal_amount": float(principal),
            "annual_interest_rate": annual_interest_rate,
            "term_months": term_months,
            "payment_frequency": payment_frequency,
            "single_payment_date": single_payment_date if is_single else None,
            "monthly_payment": float(installment),
            "total_to_receive": float(totals["total_paid"]),
            "total_interest": float(totals["total_interest"]),
            "total_profit": float(totals["total_interest"]),
            "interest_to_principal_ratio": totals["interest_to_principal_ratio"],
            "start_date": start.isoformat(),
            "schedule_preview": [
                {
                    "entry_number": e["entry_number"],
                    "due_date": e["due_date"].isoformat(),
                    "amount": float(e["amount"]),
                    "principal_portion": float(e["principal_portion"]),
                    "interest_portion": float(e["interest_portion"]),
                    "balance_after": float(e["balance_after"]),
                }
                for e in schedule[:12]
            ],
        }
