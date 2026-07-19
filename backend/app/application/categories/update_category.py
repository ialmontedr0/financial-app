"""Use case: Update a category."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

ALLOWED_UPDATE_FIELDS = {"name", "description", "category_type", "icon", "color", "sort_order", "keywords", "is_active"}


class UpdateCategoryUseCase:
    """Update a user category (partial). System categories have limited edit."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        **fields: Any,
    ) -> dict:
        """Update category fields."""
        from app.domain.categories.value_objects import CategoryType
        from app.middleware.error_handler import NotFoundError, ValidationError

        invalid = set(fields.keys()) - ALLOWED_UPDATE_FIELDS
        if invalid:
            raise ValidationError(
                f"Campos no permitidos para actualizacion: {', '.join(invalid)}"
            )

        if "name" in fields:
            name = str(fields["name"]).strip()
            if not name:
                raise ValidationError("name no puede estar vacio")
            fields["name"] = name

        if "category_type" in fields:
            try:
                CategoryType(fields["category_type"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904

        try:
            cat = await self._repo.update_category(category_id, user_id, **fields)
        except ValueError as e:
            raise ValidationError(str(e))  # noqa: B904

        if cat is None:
            raise NotFoundError("Category")

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
            "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
        }
