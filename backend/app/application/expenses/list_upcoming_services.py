"""Use case: List services with upcoming due dates."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListUpcomingServicesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, *, days_ahead: int = 30) -> dict:
        if days_ahead < 1 or days_ahead > 90:
            days_ahead = 30

        services = await self._repo.list_upcoming_services(user_id, days_ahead=days_ahead)

        items = [
            {
                "id": str(s.id),
                "name": s.name,
                "service_type": s.service_type,
                "provider_name": s.provider,
                "due_day": s.due_day,
                "estimated_amount": str(s.estimated_amount) if s.estimated_amount else None,
                "is_paid_current_month": s.payment_status == "paid",
                "category_id": str(s.category_id) if s.category_id else None,
            }
            for s in services
        ]

        return {
            "services": items,
            "total": len(items),
            "days_ahead": days_ahead,
        }
