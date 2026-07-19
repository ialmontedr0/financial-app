import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.events import EmailVerifiedEvent
from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.repositories.user_repository import UserRepository

logger = structlog.get_logger()


class VerifyEmailUseCase:
    """Verify a user's email address using a verification token."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._session_store = SessionStore()

    async def execute(self, token: str) -> dict:
        """Verify email using the token from Redis."""
        from app.middleware.error_handler import NotFoundError, ValidationError

        # Look up verification data in Redis
        data = await self._session_store.get_email_verification(token)
        if data is None:
            raise NotFoundError("Verification token")

        if data.get("purpose") != "registration":
            raise ValidationError("Invalid verification token purpose")

        user_id = uuid.UUID(data["user_id"])

        # Verify email in DB
        await self._user_repo.verify_email(user_id)

        # Delete the token (single use)
        await self._session_store.delete_email_verification(token)

        # Emit event
        user = await self._user_repo.get_by_id(user_id)
        event = EmailVerifiedEvent(
            user_id=user_id,
            email=user.email if user else "",
        )
        logger.info("email_verified", event_type=event.event_type, user_id=str(user_id))

        return {"message": "Email verified successfully"}
