"""Create a policy under an insurance."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError, ValidationError

logger = structlog.get_logger()


class CreatePolicyUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        insurance_id: uuid.UUID,
        name: str,
        description: str | None = None,
        coverage_details: str | None = None,
        deductible: float | Decimal | None = None,
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        if not name or not name.strip():
            raise ValidationError("El nombre de la póliza es requerido")
        if len(name.strip()) > 200:
            raise ValidationError("El nombre no puede exceder 200 caracteres")

        validated_deductible = None
        if deductible is not None:
            validated_deductible = Decimal(str(deductible))
            if validated_deductible < 0:
                raise ValidationError("El deducible no puede ser negativo")

        policy = await self._repo.create_policy(
            insurance_id=insurance_id,
            name=name.strip(),
            description=description,
            coverage_details=coverage_details,
            deductible=validated_deductible,
        )

        logger.info(
            "insurance_policy_created", policy_id=str(policy.id), insurance_id=str(insurance_id)
        )
        return {
            "id": str(policy.id),
            "insurance_id": str(policy.insurance_id),
            "name": policy.name,
            "description": policy.description,
            "coverage_details": policy.coverage_details,
            "deductible": float(policy.deductible) if policy.deductible else None,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
        }
