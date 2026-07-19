"""Use case: Delete a subcategory."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteSubcategoryUseCase:
    """Soft-delete a subcategory (set is_active=False)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(self, subcategory_id: uuid.UUID) -> dict:
        """Delete the subcategory."""
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete_subcategory(subcategory_id)
        if not deleted:
            raise NotFoundError("Subcategory")

        return {
            "message": "Subcategoria eliminada exitosamente",
            "subcategory_id": str(subcategory_id),
        }
