"""Use case: List categories."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListCategoriesUseCase:
    """List all visible categories (system + user's own)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        *,
        category_type: str | None = None,
        include_inactive: bool = False,
    ) -> list[dict]:
        """Return list of categories with subcategories."""
        categories = await self._repo.list_categories(
            user_id,
            category_type=category_type,
            include_inactive=include_inactive,
        )

        result: list[dict] = []
        for cat in categories:
            subs = await self._repo.list_subcategories(cat.id)
            result.append({
                "id": str(cat.id),
                "name": cat.name,
                "description": cat.description,
                "category_type": cat.category_type,
                "is_system": cat.is_system,
                "is_active": cat.is_active,
                "icon": cat.icon,
                "color": cat.color,
                "sort_order": cat.sort_order,
                "subcategories": [
                    {
                        "id": str(s.id),
                        "name": s.name,
                        "icon": s.icon,
                        "color": s.color,
                        "sort_order": s.sort_order,
                    }
                    for s in subs
                ],
                "created_at": cat.created_at.isoformat() if cat.created_at else None,
            })

        return result
