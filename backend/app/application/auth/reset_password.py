import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.events import PasswordResetEvent
from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher

logger = structlog.get_logger()


class ResetPasswordUseCase:
    """Reset a user's password using a valid reset token."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._session_repo = SessionRepository(session)
        self._session_store = SessionStore()

    async def execute(self, token: str, new_password: str) -> dict:
        """Reset the password and revoke all sessions."""
        from app.middleware.error_handler import NotFoundError, ValidationError

        # Validate token from Redis
        data = await self._session_store.get_email_verification(token)
        if data is None:
            raise NotFoundError("Password reset token")

        if data.get("purpose") != "password_reset":
            raise ValidationError("Invalid token purpose")

        user_id = uuid.UUID(data["user_id"])

        # Hash new password
        new_hash = PasswordHasher.hash_password(new_password)

        # Update password
        await self._user_repo.update_password(user_id, new_hash)

        # Delete the token
        await self._session_store.delete_email_verification(token)

        # Revoke all sessions for security
        await self._session_store.revoke_all_user_sessions(str(user_id))
        await self._session_repo.revoke_all_for_user(user_id)

        user = await self._user_repo.get_by_id(user_id)
        event = PasswordResetEvent(
            user_id=user_id,
            email=user.email if user else "",
        )
        logger.info(
            "password_reset_completed",
            event_type=event.event_type,
            user_id=str(user_id),
        )

        return {"message": "Password reset successfully. Please login again."}
