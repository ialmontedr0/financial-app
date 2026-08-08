"""Shared amortization math for lent loans (préstamo otorgado).

A lent loan is a fixed-term, fixed-installment receivable: the user lends
``principal`` and receives ``monthly_payment`` each period (principal + interest)
for ``term_months`` periods. This mirrors French amortization but from the
lender's income perspective.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

MONTHS_IN_YEAR = Decimal("12")
PERCENT_BASE = Decimal("100")


def monthly_rate(annual_rate: float) -> Decimal:
    return Decimal(str(annual_rate)) / PERCENT_BASE / MONTHS_IN_YEAR


def calculate_installment(principal: Decimal, annual_rate: float, term_months: int) -> Decimal:
    """Fixed installment: M = P * [r(1+r)^n] / [(1+r)^n - 1]."""
    if term_months <= 0:
        raise ValueError("El plazo debe ser mayor a 0")
    if annual_rate == 0:
        return (principal / Decimal(term_months)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    r = monthly_rate(annual_rate)
    n = Decimal(term_months)
    factor = (1 + r) ** n
    payment = principal * (r * factor) / (factor - 1)
    return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_schedule(
    principal_amount: float,
    annual_interest_rate: float,
    term_months: int,
    installment: Decimal,
    start_date: date,
) -> list[dict]:
    """Build the full amortization schedule (lender perspective).

    Returns a list of entries describing each receivable installment.
    The installment paid by the borrower is split into interest (income for the
    lender) and principal (return of capital). The residual ``balance`` is what
    the borrower still owes the lender.
    """
    balance = Decimal(str(principal_amount))
    r = monthly_rate(annual_interest_rate)
    entries: list[dict] = []
    current_date = start_date + timedelta(days=30)

    for i in range(1, term_months + 1):
        interest = (balance * r).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        principal_portion = (installment - interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if i == term_months:
            principal_portion = balance
            amount = principal_portion + interest
        else:
            amount = installment

        balance = (balance - principal_portion).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if balance < 0:
            balance = Decimal("0")

        entries.append(
            {
                "entry_number": i,
                "due_date": current_date,
                "amount": amount,
                "principal_portion": principal_portion,
                "interest_portion": interest,
                "balance_after": balance,
            }
        )

        # advance one calendar month keeping the day (clamped to month length)
        year = current_date.year + (current_date.month + 1 - 1) // 12
        month = (current_date.month + 1 - 1) % 12 + 1
        day = min(current_date.day, calendar.monthrange(year, month)[1])
        current_date = date(year, month, day)

    return entries


def compute_schedule_totals(principal: Decimal, term_months: int, installment: Decimal) -> dict:
    total_paid = installment * Decimal(term_months)
    total_interest = total_paid - principal
    if total_interest < 0:
        total_interest = Decimal("0")
    return {
        "total_paid": total_paid,
        "total_interest": total_interest,
        "interest_to_principal_ratio": round(float(total_interest / principal) * 100, 2)
        if principal > 0
        else 0,
    }