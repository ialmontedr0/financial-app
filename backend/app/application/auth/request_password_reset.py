
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.email.email_service import EmailService
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_service import JWTService

logger = structlog.get_logger()


class RequestPasswordResetUseCase:
    """Request a password reset token."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._session_store = SessionStore()

    async def execute(self, email: str) -> dict:
        """Generate and send a password reset token."""
        from app.domain.auth.events import PasswordResetRequestedEvent

        user = await self._user_repo.get_by_email(email)

        # Always return the same message (don't reveal if user exists)
        success_msg = "If the email exists, a password reset link has been sent"

        if user is None:
            return {"message": success_msg}

        # Generate reset token
        token = JWTService.create_access_token(
            str(user.id),
            additional_claims={"purpose": "password_reset"},
        )

        # Store in Redis with 24h TTL
        await self._session_store.store_email_verification(
            token=token,
            user_id=str(user.id),
            purpose="password_reset",
            ttl_seconds=86400,
        )

        # Send email
        await EmailService.send_password_reset_email(
            to_email=user.email,
            token=token,
            user_name=user.email.split("@")[0],
        )

        event = PasswordResetRequestedEvent(user_id=user.id, email=user.email)
        logger.info(
            "password_reset_requested",
            event_type=event.event_type,
            user_id=str(user.id),
        )

        return {"message": success_msg}
