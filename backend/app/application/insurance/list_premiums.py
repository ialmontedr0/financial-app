"""List premium installments of an insurance."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.insurance_repository import InsuranceRepository
from app.middleware.error_handler import NotFoundError

logger = structlog.get_logger()


class ListPremiumsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InsuranceRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        insurance_id: uuid.UUID,
        status: str | None = None,
    ) -> dict[str, Any]:
        insurance = await self._repo.get_insurance(insurance_id, user_id)
        if insurance is None:
            raise NotFoundError("Seguro no encontrado")

        premiums = await self._repo.list_premiums(insurance_id, status=status)
        items = [
            {
                "id": str(premium.id),
                "insurance_id": str(premium.insurance_id),
                "amount": float(premium.amount),
                "due_date": premium.due_date.isoformat(),
                "paid_date": premium.paid_date.isoformat() if premium.paid_date else None,
                "status": premium.status,
                "payment_method": premium.payment_method,
                "created_at": premium.created_at.isoformat() if premium.created_at else None,
            }
            for premium in premiums
        ]
        total_pending = sum(
            (float(p.amount) for p in premiums if p.status in ("pending", "overdue")), 0.0
        )
        return {
            "premiums": items,
            "total": len(items),
            "total_pending_amount": round(total_pending, 2),
        }
