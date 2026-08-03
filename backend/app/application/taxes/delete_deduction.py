"""Delete a tax deduction."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.tax_repository import TaxRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeleteTaxDeductionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TaxRepository(session)

    async def execute(self, user_id: uuid.UUID, deduction_id: uuid.UUID) -> dict[str, Any]:
        deduction = await self._repo.get_deduction(deduction_id, user_id)
        if deduction is None:
            raise NotFoundError("Deducción fiscal no encontrada")

        await self._repo.delete_deduction(deduction)
        logger.info("tax_deduction_deleted", deduction_id=str(deduction_id))
        return {"message": "Tax deduction deleted successfully"}
