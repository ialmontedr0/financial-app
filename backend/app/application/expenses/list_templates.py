"""Use case: List all expense templates for a user."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListTemplatesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        templates = await self._repo.list_templates(user_id)

        items = [
            {
                "id": str(t.id),
                "name": t.name,
                "default_amount": str(t.default_amount),
                "default_category_id": str(t.default_category_id)
                if t.default_category_id
                else None,
                "default_subcategory_id": str(t.default_subcategory_id)
                if t.default_subcategory_id
                else None,
                "default_account_id": str(t.default_account_id) if t.default_account_id else None,
                "default_notes": t.default_notes,
                "default_source": t.default_source,
                "usage_count": t.usage_count,
                "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
                "sort_order": t.sort_order,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in templates
        ]

        return {"templates": items, "total": len(items)}
