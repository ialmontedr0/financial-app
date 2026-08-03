"""List user tax categories."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.tax_repository import TaxRepository

logger = structlog.get_logger()


class ListTaxCategoriesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(self, user_id: uuid.UUID, tax_year: int | None = None) -> dict[str, Any]:
        categories = await self._repo.list_categories(user_id, tax_year=tax_year)
        items = [
            {
                "id": str(category.id),
                "name": category.name,
                "tax_year": category.tax_year,
                "description": category.description,
                "deduction_count": len(category.deductions),
                "created_at": category.created_at.isoformat() if category.created_at else None,
            }
            for category in categories
        ]
        return {"categories": items, "total": len(items)}
