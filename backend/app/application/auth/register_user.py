import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.auth.events import UserRegisteredEvent
from app.domain.auth.value_objects import Email, TokenPair
from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.email.email_service import EmailService
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.password_hasher import PasswordHasher

logger = structlog.get_logger()
settings = get_settings()


class RegisterUserUseCase:
    """Register a new user account."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._session_store = SessionStore()

    async def execute(
        self,
        email: str,
        password: str,
        ip_address: str = "0.0.0.0",  # noqa: S104
        user_agent: str = "unknown",
    ) -> dict:
        """Execute user registration.

        Returns dict with user data and tokens.
        """
        # Validate email format via value object
        validated_email = Email(email)

        # Check if user already exists
        existing_user = await self._user_repo.get_by_email(str(validated_email))
        if existing_user:
            from app.middleware.error_handler import ValidationError

            raise ValidationError("A user with this email already exists")

        # Hash password
        password_hash = PasswordHasher.hash_password(password)

        # Create user
        user = await self._user_repo.create(
            email=str(validated_email),
            password_hash=password_hash,
        )

        # Generate tokens
        user_id_str = str(user.id)
        access_token = JWTService.create_access_token(user_id_str)
        refresh_token = JWTService.create_refresh_token(user_id_str)

        # Decode refresh token to get JTI
        refresh_payload = JWTService.decode_token(refresh_token)
        jti = refresh_payload["jti"] if refresh_payload else str(uuid.uuid4())

        # Create session in Redis
        device_info = f"{user_agent[:50]}|{ip_address}"
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        await self._session_store.create_session(
            jti=jti,
            user_id=user_id_str,
            device_info=device_info,
            ip_address=ip_address,
            ttl_seconds=ttl_seconds,
        )
        await self._session_store.store_refresh_token(
            jti=jti,
            user_id=user_id_str,
            ttl_seconds=ttl_seconds,
        )

        # Store session in DB
        from app.infrastructure.repositories.session_repository import SessionRepository

        session_repo = SessionRepository(self._session)
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await session_repo.create(
            user_id=user.id,
            refresh_token_jti=jti,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        # Send verification email (fire and forget)
        try:
            await EmailService.send_verification_email(
                to_email=str(validated_email),
                token=access_token,  # In production, use a dedicated verification token
                user_name=str(validated_email).split("@")[0],
            )
        except Exception as exc:
            logger.warning("verification_email_failed", error=str(exc))

        # Emit domain event
        event = UserRegisteredEvent(user_id=user.id, email=str(validated_email))
        logger.info(
            "user_registered",
            event_type=event.event_type,
            user_id=str(user.id),
        )

        token_pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "mfa_enabled": user.mfa_enabled,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "tokens": token_pair.to_dict(),
        }
