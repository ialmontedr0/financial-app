"""Create a premium installment for an insurance."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.insurance.value_objects import PaymentMethod
from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class CreatePremiumUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        insurance_id: uuid.UUID,
        amount: float | Decimal,
        due_date: date,
        paid_date: date | None = None,
        payment_method: str | None = None,
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        try:
            premium_amount = Decimal(str(amount))
        except Exception as exc:  # pragma: no cover
            raise ValidationError("El monto de la prima no es válido") from exc
        if premium_amount <= 0:
            raise ValidationError("El monto de la prima debe ser mayor a 0")

        if payment_method:
            try:
                validated_method = PaymentMethod(payment_method)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
        else:
            validated_method = None

        status = (
            "paid"
            if paid_date
            else ("overdue" if due_date < datetime.now(UTC).date() else "pending")
        )

        premium = await self._repo.create_premium(
            insurance_id=insurance_id,
            amount=premium_amount,
            due_date=due_date,
            paid_date=paid_date,
            status=status,
            payment_method=validated_method.value if validated_method else None,
        )

        logger.info(
            "insurance_premium_created", premium_id=str(premium.id), insurance_id=str(insurance_id)
        )
        return {
            "id": str(premium.id),
            "insurance_id": str(premium.insurance_id),
            "amount": float(premium.amount),
            "due_date": premium.due_date.isoformat(),
            "paid_date": premium.paid_date.isoformat() if premium.paid_date else None,
            "status": premium.status,
            "payment_method": premium.payment_method,
            "created_at": premium.created_at.isoformat() if premium.created_at else None,
        }
