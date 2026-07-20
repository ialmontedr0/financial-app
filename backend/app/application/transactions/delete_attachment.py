"""Use case: Delete an attachment."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository
from app.infrastructure.storage.file_storage import delete_file

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteAttachmentUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, attachment_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        att = await self._repo.get_attachment(attachment_id)
        if att is None or att.user_id != user_id:
            raise NotFoundError("Attachment")

        delete_file(att.storage_path)
        deleted = await self._repo.delete_attachment(attachment_id)
        if not deleted:
            raise NotFoundError("Attachment")

        return {"id": str(attachment_id), "message": "Adjunto eliminado exitosamente"}
