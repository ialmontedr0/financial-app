"""Use case: delete a chat session."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.chat_repository import ChatRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DeleteChatSessionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ChatRepository(session)

    async def execute(self, user_id: uuid.UUID, session_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        deleted = await self._repo.delete_session(session_id, user_id)
        if not deleted:
            raise NotFoundError("ChatSession")
        return {"message": "Conversación eliminada"}
