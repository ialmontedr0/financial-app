"""List user tax deductions."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.tax_repository import TaxRepository

logger = structlog.get_logger()


class ListTaxDeductionsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        tax_year: int | None = None,
        category_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        deductions = await self._repo.list_deductions(
            user_id, tax_year=tax_year, category_id=category_id
        )
        items = [
            {
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
            for deduction in deductions
        ]
        return {"deductions": items, "total": len(items)}
