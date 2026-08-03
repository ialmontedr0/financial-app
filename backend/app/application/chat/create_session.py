"""Use Case: crear una sesion de chat."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.domain.chat.value_objects import MAX_TITLE_LENGTH, VALID_CHAT_TYPES
from app.infrastructure.repositories.chat_repository import ChatRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CreateChatSessionUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ChatRepository(session)

    async def execute(self, user_id: uuid.UUID, *, title: str, chat_type: str) -> dict:
        from app.middleware.error_handler import ValidationError

        if chat_type not in VALID_CHAT_TYPES:
            raise ValidationError(
                f"chat_type invalido: {chat_type}. Soportado: {', '.join(sorted(VALID_CHAT_TYPES))}"
            )

        clean_title = (title or "").strip()[:MAX_TITLE_LENGTH] or "Nueva conversación"

        session = await self._repo.create_session(user_id, title=clean_title, chat_type=chat_type)

        return {
            "id": str(session.id),
            "title": session.title,
            "chat_type": session.chat_type,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }
