"""Delete a tax category."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.tax_repository import TaxRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeleteTaxCategoryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(self, user_id: uuid.UUID, category_id: uuid.UUID) -> dict[str, Any]:
        category = await self._repo.get_category(category_id, user_id)
        if category is None:
            raise NotFoundError("Categoría fiscal no encontrada")

        await self._repo.delete_category(category)
        logger.info("tax_category_deleted", category_id=str(category_id))
        return {"message": "Tax category deleted successfully"}
