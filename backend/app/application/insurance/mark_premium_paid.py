"""Mark a premium installment as paid."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class MarkPremiumPaidUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        insurance_id: uuid.UUID,
        premium_id: uuid.UUID,
        paid_date: date | None = None,
        payment_method: str | None = None,
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        premium = await self._repo.get_premium(premium_id, insurance_id)
        if premium is None:
            raise NotFoundError("Prima no encontrada")

        if premium.status == "cancelled":
            raise ValidationError("No se puede pagar una prima cancelada")

        paid = paid_date or date.today()  # noqa: DTZ011
        updates: dict[str, Any] = {"status": "paid", "paid_date": paid}
        if payment_method:
            updates["payment_method"] = payment_method

        premium = await self._repo.update_premium(premium, **updates)
        logger.info("insurance_premium_paid", premium_id=str(premium_id))
        return {
            "id": str(premium.id),
            "insurance_id": str(premium.insurance_id),
            "amount": float(premium.amount),
            "due_date": premium.due_date.isoformat(),
            "paid_date": premium.paid_date.isoformat() if premium.paid_date else None,
            "status": premium.status,
            "payment_method": premium.payment_method,
        }
