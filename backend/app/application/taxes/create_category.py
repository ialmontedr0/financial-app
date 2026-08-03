"""Create a new tax category."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.tax.value_objects import TaxCategoryName, TaxYear
from app.infrastructure.repositories.tax_repository import TaxRepository
from app.middleware.error_handler import ValidationError

logger = structlog.get_logger()


class CreateTaxCategoryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        name: str,
        tax_year: int,
        description: str | None = None,
    ) -> dict[str, Any]:
        try:
            validated_name = TaxCategoryName(name)
            validated_year = TaxYear(tax_year)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        category = await self._repo.create_category(
            user_id=user_id,
            name=validated_name.value,
            tax_year=validated_year.value,
            description=description,
        )

        logger.info("tax_category_created", category_id=str(category.id), year=tax_year)
        return {
            "id": str(category.id),
            "name": category.name,
            "tax_year": category.tax_year,
            "description": category.description,
            "created_at": category.created_at.isoformat() if category.created_at else None,
        }
