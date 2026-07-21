"""Simulate a loan — stateless calculator."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import structlog

logger = structlog.get_logger()

MONTHS_IN_YEAR = Decimal("12")
PERCENT_BASE = Decimal("100")


class SimulateLoanUseCase:
    """Compute loan simulation without saving anything."""

    async def execute(
        self,
        principal_amount: float,
        annual_interest_rate: float,
        term_months: int,
        start_date: str | None = None,
        extra_monthly_payment: float = 0.0,
    ) -> dict:
        if principal_amount <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        if term_months <= 0 or term_months > 600:
            raise ValueError("El plazo debe estar entre 1 y 600 meses")

        principal = Decimal(str(principal_amount))
        rate = Decimal(str(annual_interest_rate))
        r = rate / PERCENT_BASE / MONTHS_IN_YEAR

        if r == 0:
            monthly_pmt = (principal / Decimal(term_months)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            n = Decimal(term_months)
            factor = (1 + r) ** n
            monthly_pmt = principal * (r * factor) / (factor - 1)
            monthly_pmt = monthly_pmt.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        extra = Decimal(str(extra_monthly_payment))

        # Build schedule
        balance = principal
        total_interest = Decimal("0")
        total_paid = Decimal("0")
        schedule = []
        disbursement = date.today()  # noqa: DTZ011
        if start_date:
            disbursement = date.fromisoformat(start_date)
        current_date = disbursement + timedelta(days=30)

        for i in range(1, term_months + 1):
            interest = (balance * r).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            principal_portion = (monthly_pmt - interest).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if i == term_months:
                principal_portion = balance
                pmt = principal_portion + interest
            else:
                pmt = monthly_pmt

            # Extra payment
            if extra > 0 and i < term_months:
                extra_principal = min(extra, balance - principal_portion)
                if extra_principal > 0:
                    principal_portion += extra_principal
                    pmt += extra_principal

            balance = (balance - principal_portion).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if balance < 0:
                balance = Decimal("0")

            total_interest += interest
            total_paid += pmt

            # Next month
            month = current_date.month + 1
            year = current_date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(current_date.day, monthrange(year, month)[1])
            current_date = date(year, month, day)

            if i <= 12 or i % 12 == 0 or i == term_months:
                schedule.append(
                    {
                        "entry_number": i,
                        "due_date": current_date.isoformat(),
                        "payment_amount": float(pmt),
                        "principal_portion": float(principal_portion),
                        "interest_portion": float(interest),
                        "balance_after": float(balance),
                    }
                )

            if balance == 0:
                break

        actual_months = len(schedule) if balance == 0 else term_months

        return {
            "principal_amount": float(principal),
            "annual_interest_rate": float(rate),
            "term_months": term_months,
            "monthly_payment": float(monthly_pmt),
            "extra_monthly_payment": float(extra),
            "total_paid": float(total_paid),
            "total_interest": float(total_interest),
            "total_cost": float(total_paid),
            "interest_to_principal_ratio": round(float(total_interest / principal * 100), 2)
            if principal > 0
            else 0,
            "actual_months": actual_months,
            "early_payoff_months": term_months - actual_months if extra > 0 else 0,
            "interest_saved_with_extra": 0.0,  # compare without extra
            "schedule_preview": schedule[:12],
        }
