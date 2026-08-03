"""Delete a policy of an insurance."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class DeletePolicyUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self, user_id: uuid.UUID, insurance_id: uuid.UUID, policy_id: uuid.UUID
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        policy = await self._repo.get_policy(policy_id, insurance_id)
        if policy is None:
            raise NotFoundError("Póliza no encontrada")

        await self._repo.delete_policy(policy)
        logger.info("insurance_policy_deleted", policy_id=str(policy_id))
        return {"message": "Policy deleted successfully"}
