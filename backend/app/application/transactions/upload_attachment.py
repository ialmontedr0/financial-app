"""Use case: Upload an attachment to a transaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository
from app.infrastructure.storage.file_storage import store_file

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}


class UploadAttachmentUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID, *,
        filename: str, content_type: str, content: bytes,
    ) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        if content_type not in ALLOWED_TYPES:
            raise ValidationError(f"Tipo de archivo no permitido: {content_type}. Permitidos: {', '.join(sorted(ALLOWED_TYPES))}")
        if len(content) > MAX_FILE_SIZE:
            raise ValidationError(f"Archivo excede el limite de {MAX_FILE_SIZE // (1024 * 1024)} MB")

        file_info = store_file(user_id=user_id, transaction_id=transaction_id, filename=filename, content=content, content_type=content_type)
        att = await self._repo.create_attachment(transaction_id, user_id, **file_info)

        return {"id": str(att.id), "transaction_id": str(att.transaction_id),
            "original_filename": att.original_filename, "mime_type": att.mime_type,
            "file_size": att.file_size, "created_at": att.created_at.isoformat() if att.created_at else None}
