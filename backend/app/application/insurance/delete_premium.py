"""Delete a premium installment of an insurance."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeletePremiumUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self, user_id: uuid.UUID, insurance_id: uuid.UUID, premium_id: uuid.UUID
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        premium = await self._repo.get_premium(premium_id, insurance_id)
        if premium is None:
            raise NotFoundError("Prima no encontrada")

        await self._repo.delete_premium(premium)
        logger.info("insurance_premium_deleted", premium_id=str(premium_id))
        return {"message": "Premium deleted successfully"}
