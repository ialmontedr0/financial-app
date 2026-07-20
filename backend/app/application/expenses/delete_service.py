"""Use case: Soft-delete an expense service."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.expense_repository import ExpenseRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteServiceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExpenseRepository(session)

    async def execute(self, user_id: uuid.UUID, service_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete_service(service_id, user_id)
        if not deleted:
            raise NotFoundError("Service")

        return {"id": str(service_id), "message": "Service eliminado exitosamente"}
