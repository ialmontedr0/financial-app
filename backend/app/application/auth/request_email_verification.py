
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.email.email_service import EmailService
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_service import JWTService

logger = structlog.get_logger()


class RequestEmailVerificationUseCase:
    """Request a new email verification token."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._session_store = SessionStore()

    async def execute(self, email: str) -> dict:
        """Generate and send a new verification email."""
        from app.middleware.error_handler import ValidationError

        user = await self._user_repo.get_by_email(email)
        if user is None:
            # Don't reveal if user exists
            return {"message": "If the email exists, a verification link has been sent"}

        if user.is_verified:
            raise ValidationError("Email is already verified")

        # Generate a verification token
        token = JWTService.create_access_token(
            str(user.id),
            additional_claims={"purpose": "registration"},
        )

        # Store in Redis with 24h TTL
        await self._session_store.store_email_verification(
            token=token,
            user_id=str(user.id),
            purpose="registration",
            ttl_seconds=86400,
        )

        # Send verification email
        await EmailService.send_verification_email(
            to_email=user.email,
            token=token,
            user_name=user.email.split("@")[0],
        )

        logger.info("verification_email_sent", user_id=str(user.id))
        return {"message": "If the email exists, a verification link has been sent"}
