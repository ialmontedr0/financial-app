from __future__ import annotations

from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.application.credit_purchases.create_credit_purchase import calculate_installment
from app.domain.credit_purchase.value_objects import FREQUENCY_MONTHS

MONTHS_IN_YEAR = Decimal("12")
PERCENT_BASE = Decimal("100")


class SimulateCreditPurchaseUseCase:
    async def execute(
        self,
        total_price: float,
        down_payment: float = 0,
        annual_interest_rate: float = 0,
        installment_count: int = 1,
        installment_frequency: str = "monthly",
        installment_amount: float | None = None,
        first_due_date: str | None = None,
    ) -> dict:
        total = Decimal(str(total_price))
        down = Decimal(str(down_payment))
        financed = total - down
        rate = Decimal(str(annual_interest_rate))

        if installment_amount is not None and installment_amount > 0:
            inst_amt = Decimal(str(installment_amount))
        else:
            inst_amt = calculate_installment(financed, rate, installment_count, installment_frequency)

        total_paid = inst_amt * Decimal(installment_count)
        total_interest = (total_paid - financed).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if total_interest < 0:
            total_interest = Decimal("0")

        first_due = datetime.now(UTC).date() + timedelta(days=30)
        if first_due_date:
            first_due = date.fromisoformat(first_due_date)

        freq_months = FREQUENCY_MONTHS.get(installment_frequency, Decimal("1"))
        periods_per_year = MONTHS_IN_YEAR / freq_months
        rate_per_period = rate / PERCENT_BASE / periods_per_year
        balance = financed

        schedule = []
        current_date = first_due

        for i in range(1, installment_count + 1):
            interest = (balance * rate_per_period).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            principal_portion = (inst_amt - interest).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if i == installment_count:
                principal_portion = balance
                payment_amount = principal_portion + interest
            else:
                payment_amount = inst_amt

            balance = (balance - principal_portion).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if balance < 0:
                balance = Decimal("0")

            schedule.append({
                "installment_number": i,
                "due_date": current_date.isoformat(),
                "amount": float(payment_amount),
                "principal_portion": float(principal_portion),
                "interest_portion": float(interest),
                "balance_after": float(balance),
            })

            months_to_add = int(freq_months)
            month = current_date.month + months_to_add
            year = current_date.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(current_date.day, monthrange(year, month)[1])
            current_date = date(year, month, day)

        return {
            "total_price": float(total),
            "down_payment": float(down),
            "financed_amount": float(financed),
            "installment_amount": float(inst_amt),
            "installment_count": installment_count,
            "total_paid": float(total_paid),
            "total_interest": float(total_interest),
            "schedule": schedule,
        }
