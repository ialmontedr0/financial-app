"""Use case: Create a subcategory."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateSubcategoryUseCase:
    """Create a subcategory under an existing category."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        **fields: Any,
    ) -> dict:
        """Create a subcategory."""
        from app.middleware.error_handler import NotFoundError, ValidationError

        cat = await self._repo.get_category_by_id(category_id, user_id)
        if cat is None:
            raise NotFoundError("Category")

        name = fields.get("name")
        if not name or not str(name).strip():
            raise ValidationError("name es requerido")
        fields["name"] = str(name).strip()
        fields["is_active"] = True

        sub = await self._repo.create_subcategory(category_id, **fields)

        return {
            "id": str(sub.id),
            "name": sub.name,
            "description": sub.description,
            "category_id": str(category_id),
            "icon": sub.icon,
            "color": sub.color,
            "sort_order": sub.sort_order,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
        }
