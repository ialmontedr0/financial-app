"""Use case: Add tags to a transaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AddTagsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID, tags: list[str]) -> dict:
        from app.middleware.error_handler import NotFoundError, ValidationError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        cleaned = [t.strip().lower() for t in tags if t.strip()]
        if not cleaned:
            raise ValidationError("Al menos un tag es requerido")
        for t in cleaned:
            if len(t) > 50:
                raise ValidationError(f"Tag excede 50 caracteres: {t}")

        added = await self._repo.add_tags(transaction_id, user_id, cleaned)
        all_tags = await self._repo.get_tags(transaction_id)
        return {"transaction_id": str(transaction_id), "added": [t.tag_name for t in added],
            "total_tags": len(all_tags), "all_tags": [t.tag_name for t in all_tags]}
