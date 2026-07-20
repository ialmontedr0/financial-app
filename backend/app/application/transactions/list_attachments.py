"""Use case: List attachments for a transaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListAttachmentsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        attachments = await self._repo.list_attachments(transaction_id)
        return {"transaction_id": str(transaction_id), "attachments": [
            {"id": str(a.id), "original_filename": a.original_filename, "mime_type": a.mime_type,
             "file_size": a.file_size, "created_at": a.created_at.isoformat() if a.created_at else None}
            for a in attachments], "total": len(attachments)}
