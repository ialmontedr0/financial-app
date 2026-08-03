"""Update a tax deduction."""

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


class UpdateTaxDeductionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        deduction_id: uuid.UUID,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        deduction = await self._repo.get_deduction(deduction_id, user_id)
        if deduction is None:
            raise NotFoundError("Deducción fiscal no encontrada")

        updates: dict[str, Any] = {}

        if "description" in fields and fields["description"] is not None:
            try:
                updates["description"] = TaxDeductionDescription(fields["description"]).value
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

        if "amount" in fields and fields["amount"] is not None:
            try:
                amount = MoneyAmount(Decimal(str(fields["amount"])))
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            if amount.value <= 0:
                raise ValidationError("El monto de la deducción debe ser mayor a 0")
            updates["amount"] = amount.value

        if "date" in fields and fields["date"] is not None:
            updates["date"] = date.fromisoformat(fields["date"])

        if "deductible" in fields:
            if fields["deductible"] is None:
                updates["deductible"] = None
            else:
                try:
                    deductible = MoneyAmount(Decimal(str(fields["deductible"])))
                except ValueError as exc:
                    raise ValidationError(str(exc)) from exc
                updates["deductible"] = deductible.value

        if "tax_year" in fields and fields["tax_year"] is not None:
            try:
                updates["tax_year"] = TaxYear(fields["tax_year"]).value
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

        if "receipt_url" in fields:
            updates["receipt_url"] = fields["receipt_url"]

        if "category_id" in fields:
            if fields["category_id"] is None:
                updates["category_id"] = None
            else:
                category_id = uuid.UUID(fields["category_id"])
                category = await self._repo.get_category(category_id, user_id)
                if category is None:
                    raise NotFoundError("Categoría fiscal no encontrada")
                updates["category_id"] = category_id

        if updates:
            deduction = await self._repo.update_deduction(deduction, **updates)

        return {
            "id": str(deduction.id),
            "category_id": str(deduction.category_id) if deduction.category_id else None,
            "description": deduction.description,
            "amount": float(deduction.amount),
            "date": deduction.date.isoformat(),
            "deductible": float(deduction.deductible) if deduction.deductible else None,
            "tax_year": deduction.tax_year,
            "receipt_url": deduction.receipt_url,
        }
