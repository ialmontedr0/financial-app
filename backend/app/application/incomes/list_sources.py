"""Use case: List income sources."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListSourcesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        is_active: bool | None = None,
        income_type: str | None = None,
    ) -> dict:
        sources = await self._repo.list_sources(user_id, is_active=is_active, income_type=income_type)

        items = [
            {
                "id": str(s.id),
                "name": s.name,
                "income_type": s.income_type,
                "stability": s.stability,
                "frequency": s.frequency,
                "expected_amount": str(s.default_amount) if s.default_amount else None,
                "default_account_id": str(s.default_account_id) if s.default_account_id else None,
                "default_category_id": str(s.default_category_id) if s.default_category_id else None,
                "default_currency": s.default_currency,
                "is_active": s.is_active,
                "total_received": str(s.total_received) if s.total_received else "0",
                "income_count": s.income_count,
                "last_received_at": s.last_received_at.isoformat() if s.last_received_at else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sources
        ]

        return {"sources": items, "total": len(items)}
