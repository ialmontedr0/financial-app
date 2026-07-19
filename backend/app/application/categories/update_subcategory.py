"""Use case: Update a subcategory."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UpdateSubcategoryUseCase:
    """Update a subcategory (partial)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(
        self,
        subcategory_id: uuid.UUID,
        **fields: Any,
    ) -> dict:
        """Update subcategory fields."""
        from app.middleware.error_handler import NotFoundError

        sub = await self._repo.update_subcategory(subcategory_id, **fields)
        if sub is None:
            raise NotFoundError("Subcategory")

        return {
            "id": str(sub.id),
            "name": sub.name,
            "description": sub.description,
            "category_id": str(sub.category_id),
            "icon": sub.icon,
            "color": sub.color,
            "sort_order": sub.sort_order,
            "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
        }
