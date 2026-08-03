"""List user insurances."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository

logger = structlog.get_logger()


class ListInsurancesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        type: str | None = None,  # noqa: A002
    ) -> dict[str, Any]:
        insurances = await self._repo.list_insurances(user_id, status=status, type=type)
        items = [
            {
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
                "policies_count": len(insurance.policies),
                "created_at": insurance.created_at.isoformat() if insurance.created_at else None,
            }
            for insurance in insurances
        ]
        return {"insurances": items, "total": len(items)}
