import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.events import UserSessionRevokedEvent
from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.repositories.session_repository import SessionRepository

logger = structlog.get_logger()


class LogoutUserUseCase:
    """Logout a user: revoke current session or all sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._session_repo = SessionRepository(session)
        self._session_store = SessionStore()

    async def execute_logout(self, refresh_token_jti: str) -> None:
        """Revoke a single session."""
        # Remove from Redis
        await self._session_store.delete_refresh_token(refresh_token_jti)
        await self._session_store.delete_session(refresh_token_jti)

        # Revoke in DB
        await self._session_repo.revoke(refresh_token_jti)

        event = UserSessionRevokedEvent(session_jti=refresh_token_jti, revoked_all=False)
        logger.info("session_revoked", event_type=event.event_type, jti=refresh_token_jti)

    async def execute_logout_all(self, user_id: uuid.UUID) -> int:
        """Revoke all sessions for a user."""
        user_id_str = str(user_id)

        # Remove from Redis
        count = await self._session_store.revoke_all_user_sessions(user_id_str)

        # Revoke in DB
        db_count = await self._session_repo.revoke_all_for_user(user_id)

        event = UserSessionRevokedEvent(
            user_id=user_id,
            revoked_all=True,
        )
        logger.info(
            "all_sessions_revoked",
            event_type=event.event_type,
            user_id=user_id_str,
            count=count,
        )

        return count
