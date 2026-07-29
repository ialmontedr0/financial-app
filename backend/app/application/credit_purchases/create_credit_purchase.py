from __future__ import annotations

import uuid
from calendar import monthrange
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.credit_purchase.value_objects import FREQUENCY_MONTHS
from app.infrastructure.repositories.credit_purchase_repository import CreditPurchaseRepository
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()
MONTHS_IN_YEAR = Decimal("12")
PERCENT_BASE = Decimal("100")


def calculate_installment(
    financed: Decimal, annual_rate: Decimal, num_installments: int, frequency: str
) -> Decimal:
    if annual_rate == 0:
        return (financed / Decimal(num_installments)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    freq_months = FREQUENCY_MONTHS.get(frequency, Decimal("1"))
    periods_per_year = MONTHS_IN_YEAR / freq_months
    rate_per_period = annual_rate / PERCENT_BASE / periods_per_year
    n = Decimal(num_installments)
    if rate_per_period == 0:
        return (financed / n).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    factor = (1 + rate_per_period) ** n
    payment = financed * (rate_per_period * factor) / (factor - 1)
    return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def generate_installment_schedule(
    financed: Decimal,
    annual_rate: Decimal,
    num_installments: int,
    installment_amount: Decimal,
    frequency: str,
    first_due: date,
) -> list[dict]:
    entries = []
    balance = financed
    freq_months = FREQUENCY_MONTHS.get(frequency, Decimal("1"))
    periods_per_year = MONTHS_IN_YEAR / freq_months
    rate_per_period = annual_rate / PERCENT_BASE / periods_per_year
    total_interest = Decimal("0")

    current_date = first_due

    for i in range(1, num_installments + 1):
        interest = (balance * rate_per_period).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        principal_portion = (installment_amount - interest).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if i == num_installments:
            principal_portion = balance
            payment_amount = principal_portion + interest
        else:
            payment_amount = installment_amount

        balance = (balance - principal_portion).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if balance < 0:
            balance = Decimal("0")

        total_interest += interest

        entries.append({
            "installment_number": i,
            "due_date": current_date,
            "amount": payment_amount,
            "principal_portion": principal_portion,
            "interest_portion": interest,
            "balance_after": balance,
            "status": "pending",
        })

        months_to_add = int(freq_months)
        month = current_date.month + months_to_add
        year = current_date.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        day = min(current_date.day, monthrange(year, month)[1])
        current_date = date(year, month, day)

    return entries


class CreateCreditPurchaseUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CreditPurchaseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        item_name: str,
        total_price: float,
        store_name: str | None = None,
        description: str | None = None,
        down_payment: float = 0,
        annual_interest_rate: float = 0,
        installment_count: int = 1,
        installment_frequency: str = "monthly",
        installment_amount: float | None = None,
        purchase_date: str | None = None,
        first_due_date: str | None = None,
        notes: str | None = None,
    ) -> dict:
        if not item_name or not item_name.strip():
            raise ValidationError("El nombre del articulo es requerido")
        if total_price <= 0:
            raise ValidationError("El precio debe ser mayor a 0")
        if installment_count < 1:
            raise ValidationError("Debe haber al menos 1 cuota")
        if down_payment < 0:
            raise ValidationError("El pago inicial no puede ser negativo")
        if down_payment >= total_price:
            raise ValidationError("El pago inicial no puede ser mayor o igual al precio total")

        total_dec = Decimal(str(total_price))
        down_dec = Decimal(str(down_payment))
        financed = total_dec - down_dec
        rate = Decimal(str(annual_interest_rate))

        if installment_amount is not None and installment_amount > 0:
            inst_amt = Decimal(str(installment_amount))
            calc_method = "manual"
        else:
            inst_amt = calculate_installment(financed, rate, installment_count, installment_frequency)
            calc_method = "auto"

        total_interest = (inst_amt * Decimal(installment_count) - financed).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if total_interest < 0:
            total_interest = Decimal("0")

        purchase_dt = datetime.now(UTC).date()
        if purchase_date:
            purchase_dt = date.fromisoformat(purchase_date)

        first_due = purchase_dt + timedelta(days=30)
        if first_due_date:
            first_due = date.fromisoformat(first_due_date)

        purchase = await self._repo.create(
            user_id=user_id,
            item_name=item_name.strip(),
            store_name=store_name,
            description=description,
            total_price=total_dec,
            down_payment=down_dec,
            financed_amount=financed,
            annual_interest_rate=rate,
            installment_count=installment_count,
            installment_frequency=installment_frequency,
            installment_amount=inst_amt,
            calculation_method=calc_method,
            total_interest=total_interest,
            purchase_date=purchase_dt,
            first_due_date=first_due,
            status="active",
            notes=notes,
        )

        schedule = generate_installment_schedule(
            financed, rate, installment_count, inst_amt, installment_frequency, first_due
        )
        await self._repo.create_installments(purchase.id, schedule)

        logger.info(
            "credit_purchase_created",
            id=str(purchase.id),
            item=item_name,
            installments=len(schedule),
        )

        return {
            "id": str(purchase.id),
            "item_name": purchase.item_name,
            "store_name": purchase.store_name,
            "total_price": float(purchase.total_price),
            "down_payment": float(purchase.down_payment),
            "financed_amount": float(purchase.financed_amount),
            "annual_interest_rate": float(purchase.annual_interest_rate),
            "installment_count": purchase.installment_count,
            "installment_frequency": purchase.installment_frequency,
            "installment_amount": float(purchase.installment_amount),
            "calculation_method": purchase.calculation_method,
            "total_interest": float(purchase.total_interest),
            "purchase_date": purchase.purchase_date.isoformat(),
            "first_due_date": purchase.first_due_date.isoformat(),
            "status": purchase.status,
            "installments_count": len(schedule),
            "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
        }
