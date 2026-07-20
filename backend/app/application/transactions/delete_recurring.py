"""Use case: Delete a recurring pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteRecurringUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, recurring_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.soft_delete_recurring(recurring_id, user_id)
        if not deleted:
            raise NotFoundError("Recurring Pattern")

        return {"id": str(recurring_id), "message": "Patron recurrente eliminado exitosamente"}
