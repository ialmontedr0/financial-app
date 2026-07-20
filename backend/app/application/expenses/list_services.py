"""Use case: List expense services with optional filters."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListServicesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        is_active: bool | None = None,
        service_type: str | None = None,
    ) -> dict:
        services = await self._repo.list_services(
            user_id, is_active=is_active, service_type=service_type
        )

        items = [
            {
                "id": str(s.id),
                "name": s.name,
                "service_type": s.service_type,
                "provider_name": s.provider,
                "account_number": s.account_number,
                "category_id": str(s.category_id) if s.category_id else None,
                "due_day": s.due_day,
                "estimated_amount": str(s.estimated_amount) if s.estimated_amount else None,
                "is_active": s.is_active,
                "is_paid_current_month": s.payment_status == "paid",
                "notes": s.notes,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in services
        ]

        return {"services": items, "total": len(items)}
