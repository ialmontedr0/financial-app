"""Use case: get a session with its message history."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.chat_repository import ChatRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetChatSessionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ChatRepository(session)

    async def execute(self, user_id: uuid.UUID, session_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        session = await self._repo.get_session(session_id, user_id)
        if session is None:
            raise NotFoundError("ChatSession")

        messages = await self._repo.list_messages(session_id)

        return {
            "id": str(session.id),
            "title": session.title,
            "chat_type": session.chat_type,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }
