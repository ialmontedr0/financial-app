"""Use case: Delete a user category."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteCategoryUseCase:
    """Soft-delete a user category. System categories cannot be deleted."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(self, user_id: uuid.UUID, category_id: uuid.UUID) -> dict:
        """Delete the category."""
        from app.middleware.error_handler import NotFoundError, ValidationError

        cat = await self._repo.get_category_by_id(category_id, user_id)
        if cat is None:
            raise NotFoundError("Category")

        if cat.is_system:
            raise ValidationError("No se pueden eliminar categorias del sistema")

        deleted = await self._repo.delete_category(category_id, user_id)
        if not deleted:
            raise NotFoundError("Category")

        return {
            "message": f"Categoria '{cat.name}' eliminada exitosamente",
            "category_id": str(category_id),
        }
