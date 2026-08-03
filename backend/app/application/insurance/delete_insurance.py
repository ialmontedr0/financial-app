"""Delete an insurance policy (soft delete)."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeleteInsuranceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(self, user_id: uuid.UUID, insurance_id: uuid.UUID) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        await self._repo.delete_insurance(insurance)
        logger.info("insurance_deleted", insurance_id=str(insurance_id))
        return {"message": "Insurance deleted successfully"}
