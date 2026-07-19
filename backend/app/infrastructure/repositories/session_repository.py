import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user_session import UserSessionModel

logger = structlog.get_logger()


class SessionRepository:
    """Repository for user session persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        refresh_token_jti: str,
        device_info: str,
        ip_address: str,
        user_agent: str,
        expires_at: datetime,
    ) -> UserSessionModel:
        """Create a new session record."""
        session_model = UserSessionModel(
            user_id=user_id,
            refresh_token_jti=refresh_token_jti,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        self._session.add(session_model)
        await self._session.flush()
        logger.info(
            "session_record_created",
            session_id=str(session_model.id),
            user_id=str(user_id),
        )
        return session_model

    async def get_by_jti(self, jti: str) -> UserSessionModel | None:
        """Get a session by refresh token JTI."""
        stmt = select(UserSessionModel).where(
            UserSessionModel.refresh_token_jti == jti,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, jti: str) -> None:
        """Revoke a single session."""
        stmt = (
            update(UserSessionModel)
            .where(UserSessionModel.refresh_token_jti == jti)
            .values(is_revoked=True)
        )
        await self._session.execute(stmt)
        logger.info("session_revoked", jti=jti)

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        """Revoke all sessions for a user. Returns count revoked."""
        stmt = (
            update(UserSessionModel)
            .where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.is_revoked == False,  # noqa: E712
            )
            .values(is_revoked=True)
        )
        result = await self._session.execute(stmt)
        count = result.rowcount
        logger.info("all_sessions_revoked", user_id=str(user_id), count=count)
        return count

    async def get_active_sessions(self, user_id: uuid.UUID) -> list[UserSessionModel]:
        """Get all active (non-revoked, non-expired) sessions for a user."""
        stmt = (
            select(UserSessionModel)
            .where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.is_revoked == False,  # noqa: E712
                UserSessionModel.expires_at > datetime.now(UTC),
            )
            .order_by(UserSessionModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_expired(self) -> int:
        """Delete expired sessions. Returns count deleted."""
        from sqlalchemy import delete

        stmt = delete(UserSessionModel).where(
            UserSessionModel.expires_at < datetime.now(UTC),
        )
        result = await self._session.execute(stmt)
        return result.rowcount
