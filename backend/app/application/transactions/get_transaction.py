"""Use case: Get transaction detail."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetTransactionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        tags = await self._repo.get_tags(tx.id)
        attachments = await self._repo.list_attachments(tx.id)

        return {
            "id": str(tx.id), "account_id": str(tx.account_id),
            "category_id": str(tx.category_id) if tx.category_id else None,
            "subcategory_id": str(tx.subcategory_id) if tx.subcategory_id else None,
            "transaction_type": tx.transaction_type, "status": tx.status,
            "amount": str(tx.amount), "currency_code": tx.currency_code,
            "description": tx.description, "notes": tx.notes,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "transfer_id": str(tx.transfer_id) if tx.transfer_id else None,
            "source": tx.source, "recurring_id": str(tx.recurring_id) if tx.recurring_id else None,
            "ai_category_id": str(tx.ai_category_id) if tx.ai_category_id else None,
            "ai_confidence": str(tx.ai_confidence) if tx.ai_confidence else None,
            "ai_model_version": tx.ai_model_version, "ai_reason": tx.ai_reason,
            "tags": [t.tag_name for t in tags],
            "attachments": [{"id": str(a.id), "original_filename": a.original_filename, "mime_type": a.mime_type,
                "file_size": a.file_size, "created_at": a.created_at.isoformat() if a.created_at else None} for a in attachments],
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
        }
