"""Use case: Soft-delete an expense template."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteTemplateUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, template_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete_template(template_id, user_id)
        if not deleted:
            raise NotFoundError("Template")

        return {"id": str(template_id), "message": "Template eliminado exitosamente"}
