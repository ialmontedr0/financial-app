"""Get a single insurance policy."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class GetInsuranceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(self, user_id: uuid.UUID, insurance_id: uuid.UUID) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        return {
            "id": str(insurance.id),
            "name": insurance.name,
            "type": insurance.type,
            "provider": insurance.provider,
            "policy_number": insurance.policy_number,
            "status": insurance.status,
            "start_date": insurance.start_date.isoformat(),
            "end_date": insurance.end_date.isoformat() if insurance.end_date else None,
            "coverage_amount": float(insurance.coverage_amount)
            if insurance.coverage_amount
            else None,
            "premium_amount": float(insurance.premium_amount),
            "premium_frequency": insurance.premium_frequency,
            "notes": insurance.notes,
            "policies": [
                {
                    "id": str(policy.id),
                    "name": policy.name,
                    "description": policy.description,
                    "coverage_details": policy.coverage_details,
                    "deductible": float(policy.deductible) if policy.deductible else None,
                }
                for policy in insurance.policies
            ],
            "premiums_count": len(insurance.premiums),
            "created_at": insurance.created_at.isoformat() if insurance.created_at else None,
        }
