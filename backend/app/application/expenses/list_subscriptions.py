"""Use case: List subscriptions with optional status filter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListSubscriptionsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, *, status: str | None = None) -> dict:
        valid_statuses = {"active", "paused", "cancelled", "trial", "expired", None}
        if status not in valid_statuses:
            status = None

        subs = await self._repo.list_subscriptions(user_id, status=status)

        items = [
            {
                "id": str(s.id),
                "name": s.name,
                "amount": str(s.amount),
                "billing_frequency": s.billing_frequency,
                "status": s.status,
                "category_id": str(s.category_id) if s.category_id else None,
                "start_date": s.start_date.isoformat() if s.start_date else None,
                "end_date": s.end_date.isoformat() if s.end_date else None,
                "website_url": s.website_url,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ]

        return {"subscriptions": items, "total": len(items)}
