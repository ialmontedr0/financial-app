"""Create a new tax deduction."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.tax.value_objects import (
    MoneyAmount,
    TaxDeductionDescription,
    TaxYear,
)
from app.infrastructure.repositories.tax_repository import TaxRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class CreateTaxDeductionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        description: str,
        amount: float | Decimal,
        date_value: date,
        tax_year: int,
        category_id: uuid.UUID | None = None,
        deductible: float | Decimal | None = None,
        receipt_url: str | None = None,
    ) -> dict[str, Any]:
        try:
            validated_description = TaxDeductionDescription(description)
            validated_amount = MoneyAmount(Decimal(str(amount)))
            validated_year = TaxYear(tax_year)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        if validated_amount.value <= 0:
            raise ValidationError("El monto de la deducción debe ser mayor a 0")

        if deductible is not None:
            validated_deductible = MoneyAmount(Decimal(str(deductible)))
            if validated_deductible.value < 0:
                raise ValidationError("El monto deducible no puede ser negativo")
        else:
            validated_deductible = None

        if category_id:
            category = await self._repo.get_category(category_id, user_id)
            if category is None:
                raise NotFoundError("Categoría fiscal no encontrada")

        deduction = await self._repo.create_deduction(
            user_id=user_id,
            category_id=category_id,
            description=validated_description.value,
            amount=validated_amount.value,
            date=date_value,
            deductible=validated_deductible.value if validated_deductible else None,
            tax_year=validated_year.value,
            receipt_url=receipt_url,
        )

        logger.info("tax_deduction_created", deduction_id=str(deduction.id), year=tax_year)
        return {
            "id": str(deduction.id),
            "category_id": str(deduction.category_id) if deduction.category_id else None,
            "description": deduction.description,
            "amount": float(deduction.amount),
            "date": deduction.date.isoformat(),
            "deductible": float(deduction.deductible) if deduction.deductible else None,
            "tax_year": deduction.tax_year,
            "receipt_url": deduction.receipt_url,
            "created_at": deduction.created_at.isoformat() if deduction.created_at else None,
        }
