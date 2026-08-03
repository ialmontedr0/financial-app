"""List policies of an insurance."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class ListPoliciesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(self, user_id: uuid.UUID, insurance_id: uuid.UUID) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        policies = await self._repo.list_policies(insurance_id)
        items = [
            {
                "id": str(policy.id),
                "insurance_id": str(policy.insurance_id),
                "name": policy.name,
                "description": policy.description,
                "coverage_details": policy.coverage_details,
                "deductible": float(policy.deductible) if policy.deductible else None,
                "created_at": policy.created_at.isoformat() if policy.created_at else None,
            }
            for policy in policies
        ]
        return {"policies": items, "total": len(items)}
