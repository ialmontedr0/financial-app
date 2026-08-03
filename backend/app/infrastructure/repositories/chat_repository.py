"""Repositorio para sesiones y mensajes del chat."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from app.infrastructure.models.chat import ChatMessageModel, ChatSessionModel

if TYPE_CHECKING:
    import uuid
    from datetime import datetime  # noqa: F401

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Sessions -----------------------------------------------------------

    async def create_session(
        self, user_id: uuid.UUID, *, title: str, chat_type: str
    ) -> ChatSessionModel:
        session = ChatSessionModel(user_id=user_id, title=title, chat_type=chat_type)
        self._session.add(session)
        await self._session.flush()
        return session

    async def get_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChatSessionModel | None:
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id,
            ChatSessionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(self, user_id: uuid.UUID, *, limit: int = 50) -> list[ChatSessionModel]:
        stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.user_id == user_id, ChatSessionModel.deleted_at.is_(None))
            .order_by(ChatSessionModel.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime

        session = await self.get_session(session_id, user_id)
        if session is None:
            return False
        session.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def touch_session(self, session_id: uuid.UUID) -> None:
        from datetime import UTC, datetime

        session = await self._session.get(ChatSessionModel, session_id)
        if session is not None:
            session.updated_at = datetime.now(UTC)
            await self._session.flush()

    # --- Messages -----------------------------------------------------------
    async def list_messages(self, session_id: uuid.UUID) -> list[ChatMessageModel]:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self, session_id: uuid.UUID, *, role: str, content: str
    ) -> ChatMessageModel:
        message = ChatMessageModel(session_id=session_id, role=role, content=content)
        self._session.add(message)
        await self._session.flush()
        return message
