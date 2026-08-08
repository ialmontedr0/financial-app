"""Use case: revoke a single user session by id (ownership enforced)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog

from app.domain.auth.events import UserSessionRevokedEvent
from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.repositories.session_repository import SessionRepository
from app.middleware.error_handler import NotFoundError, UnauthorizedError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class RevokeSessionUseCase:
    """Revoke one specific session belonging to the authenticated user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SessionRepository(session)
        self._store = SessionStore()

    async def execute(self, user_id: uuid.UUID, session_id: str) -> dict:
        """Revoke the session if owned by the user; raise otherwise."""
        parsed_id = uuid.UUID(session_id)
        existing = await self._repo.get_active_by_id_for_user(parsed_id, user_id)
        if existing is None:
            raise NotFoundError("Sesion no encontrada")

        revoked = await self._repo.revoke_by_id_for_user(parsed_id, user_id)
        await self._store.delete_session(existing.refresh_token_jti)
        await self._store.delete_refresh_token(existing.refresh_token_jti)

        event = UserSessionRevokedEvent(user_id=user_id, session_jti=existing.refresh_token_jti, revoked_all=False)
        logger.info("session_revoked_by_user", event_type=event.event_type, session_id=str(parsed_id))

        return {"session_id": str(parsed_id), "message": "Sesion revocada"}