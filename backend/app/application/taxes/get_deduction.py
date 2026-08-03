"""Get a single tax deduction."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.tax_repository import TaxRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetTaxDeductionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(self, user_id: uuid.UUID, deduction_id: uuid.UUID) -> dict[str, Any]:
        deduction = await self._repo.get_deduction(deduction_id, user_id)
        if deduction is None:
            raise NotFoundError("Deducción fiscal no encontrada")

        return {
            "id": str(deduction.id),
            "category_id": str(deduction.category_id) if deduction.category_id else None,
            "category_name": deduction.category.name if deduction.category else None,
            "description": deduction.description,
            "amount": float(deduction.amount),
            "date": deduction.date.isoformat(),
            "deductible": float(deduction.deductible) if deduction.deductible else None,
            "tax_year": deduction.tax_year,
            "receipt_url": deduction.receipt_url,
            "created_at": deduction.created_at.isoformat() if deduction.created_at else None,
        }
