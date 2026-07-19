"""Use case: Create a new category."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateCategoryUseCase:
    """Create a new user category."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(self, user_id: uuid.UUID, **fields: Any) -> dict:
        """Create a new category for the user."""
        from app.domain.categories.value_objects import CategoryType
        from app.middleware.error_handler import ValidationError

        name = fields.get("name")
        if not name or not str(name).strip():
            raise ValidationError("name es requerido")
        fields["name"] = str(name).strip()

        category_type = fields.get("category_type", "expense")
        try:
            CategoryType(category_type)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904
        fields["category_type"] = category_type

        # User categories are never system
        fields["is_system"] = False
        fields["is_active"] = True

        category = await self._repo.create_category(user_id, **fields)

        return {
            "id": str(category.id),
            "name": category.name,
            "description": category.description,
            "category_type": category.category_type,
            "is_system": category.is_system,
            "is_active": category.is_active,
            "icon": category.icon,
            "color": category.color,
            "sort_order": category.sort_order,
            "created_at": category.created_at.isoformat() if category.created_at else None,
        }
