"""Use case: Remove a tag from a transaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RemoveTagUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID, tag_name: str) -> dict:
        from app.middleware.error_handler import NotFoundError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        removed = await self._repo.remove_tag(transaction_id, tag_name.strip().lower())
        if not removed:
            raise NotFoundError("Tag")

        all_tags = await self._repo.get_tags(transaction_id)
        return {"transaction_id": str(transaction_id), "removed_tag": tag_name.strip().lower(),
            "remaining_tags": [t.tag_name for t in all_tags]}
