"""Use case: Get a single category."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetCategoryUseCase:
    """Get a single category by ID with subcategories."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(self, user_id: uuid.UUID, category_id: uuid.UUID) -> dict:
        """Return a single category with its subcategories."""
        from app.middleware.error_handler import NotFoundError

        cat = await self._repo.get_category_by_id(category_id, user_id)
        if cat is None:
            raise NotFoundError("Category")

        subs = await self._repo.list_subcategories(category_id)

        return {
            "id": str(cat.id),
            "name": cat.name,
            "description": cat.description,
            "category_type": cat.category_type,
            "is_system": cat.is_system,
            "is_active": cat.is_active,
            "icon": cat.icon,
            "color": cat.color,
            "sort_order": cat.sort_order,
            "keywords": cat.keywords,
            "subcategories": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "description": s.description,
                    "icon": s.icon,
                    "color": s.color,
                    "sort_order": s.sort_order,
                    "keywords": s.keywords,
                }
                for s in subs
            ],
            "created_at": cat.created_at.isoformat() if cat.created_at else None,
            "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
        }
