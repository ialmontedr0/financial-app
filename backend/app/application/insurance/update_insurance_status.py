"""Update the status of an insurance policy."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.insurance.value_objects import InsuranceStatus
from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class UpdateInsuranceStatusUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self, user_id: uuid.UUID, insurance_id: uuid.UUID, status: str
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        try:
            validated = InsuranceStatus(status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        insurance = await self._repo.update_insurance(insurance, status=validated.value)
        logger.info("insurance_status_updated", insurance_id=str(insurance_id), status=status)
        return {"id": str(insurance.id), "status": insurance.status}
