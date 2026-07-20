"""Use case: Soft-delete an income source."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.income_repository import IncomeRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteSourceUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IncomeRepository(session)

    async def execute(self, user_id: uuid.UUID, source_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete_source(source_id, user_id)
        if not deleted:
            raise NotFoundError("IncomeSource")

        return {
            "id": str(source_id),
            "message": "IncomeSource eliminado exitosamente",
        }
