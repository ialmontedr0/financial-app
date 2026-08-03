"""Use case: list chat sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.chat_repository import ChatRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ListChatSessionsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ChatRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        sessions = await self._repo.list_sessions(user_id)
        items = [
            {
                "id": str(s.id),
                "title": s.title,
                "chat_type": s.chat_type,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ]
        return {"sessions": items, "total": len(items)}
