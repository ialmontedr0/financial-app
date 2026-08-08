"""Simulate a lent loan (préstamo otorgado) — stateless calculator."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.application.lent_loans.amortization import (
    calculate_installment,
    compute_schedule_totals,
    generate_schedule,
)
from app.middleware.error_handler import ValidationError


class SimulateLentLoanUseCase:
    """Compute installments, totals and schedule without saving anything."""

    def __init__(self, session=None) -> None:
        self._session = session

    async def execute(
        self,
        principal_amount: float,
        annual_interest_rate: float,
        term_months: int,
        start_date: str | None = None,
    ) -> dict:
        if principal_amount <= 0:
            raise ValidationError("El monto prestado debe ser mayor a 0")
        if annual_interest_rate < 0:
            raise ValidationError("La tasa de interés no puede ser negativa")
        if term_months <= 0 or term_months > 600:
            raise ValidationError("El plazo debe estar entre 1 y 600 meses")

        principal = Decimal(str(principal_amount))
        installment = calculate_installment(principal, annual_interest_rate, term_months)

        start = date.today()
        if start_date:
            start = date.fromisoformat(start_date)

        schedule = generate_schedule(
            principal_amount, annual_interest_rate, term_months, installment, start
        )

        totals = compute_schedule_totals(principal, term_months, installment)

        return {
            "principal_amount": float(principal),
            "annual_interest_rate": annual_interest_rate,
            "term_months": term_months,
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