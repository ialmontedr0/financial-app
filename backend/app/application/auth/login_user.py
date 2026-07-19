import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.auth.events import UserLoggedInEvent
from app.domain.auth.value_objects import TokenPair
from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.mfa_service import MFAService
from app.infrastructure.security.password_hasher import PasswordHasher

logger = structlog.get_logger()
settings = get_settings()


class LoginUserUseCase:
    """Authenticate a user with email and password.

    Supports MFA: if enabled, returns requires_mfa=True
    and the client must call /mfa/verify to complete login.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._session_repo = SessionRepository(session)
        self._session_store = SessionStore()

    async def execute(
        self,
        email: str,
        password: str,
        ip_address: str = "0.0.0.0",  # noqa: S104
        user_agent: str = "unknown",
    ) -> dict:
        """Execute user login.

        Returns dict with tokens or requires_mfa flag.
        """
        from app.middleware.error_handler import UnauthorizedError

        # Find user
        user = await self._user_repo.get_by_email(email)
        if user is None:
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        # Verify password
        if not PasswordHasher.verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        user_id_str = str(user.id)

        # Check MFA
        if user.mfa_enabled:
            # Generate a temporary MFA token (short-lived, only for MFA verification)
            mfa_token = JWTService.create_access_token(
                user_id_str,
                additional_claims={"mfa_pending": True},
            )
            logger.info("mfa_challenge_required", user_id=user_id_str)
            return {
                "requires_mfa": True,
                "mfa_token": mfa_token,
                "message": "MFA verification required",
            }

        # No MFA — issue full tokens
        tokens = await self._issue_tokens(user_id_str, ip_address, user_agent)

        # Update login info
        await self._user_repo.update_login_info(user.id)

        # Emit event
        event = UserLoggedInEvent(
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info("user_logged_in", event_type=event.event_type, user_id=user_id_str)

        return {
            "requires_mfa": False,
            "user": {
                "id": user_id_str,
                "email": user.email,
                "role": user.role,
                "mfa_enabled": user.mfa_enabled,
            },
            "tokens": tokens.to_dict(),
        }

    async def complete_mfa_login(
        self,
        mfa_token: str,
        mfa_code: str,
        ip_address: str = "0.0.0.0",  # noqa: S104
        user_agent: str = "unknown",
    ) -> dict:
        """Complete login after MFA verification."""
        from app.middleware.error_handler import UnauthorizedError

        # Decode MFA token
        payload = JWTService.verify_token(mfa_token, expected_type="access")
        if payload is None:
            raise UnauthorizedError("Invalid or expired MFA token")

        if not payload.get("mfa_pending"):
            raise UnauthorizedError("Invalid MFA token")

        user_id_str = payload["sub"]
        user = await self._user_repo.get_by_id(uuid.UUID(user_id_str))
        if user is None:
            raise UnauthorizedError("User not found")

        # Verify MFA code
        if not user.mfa_secret:
            raise UnauthorizedError("MFA not configured")

        if not MFAService.verify_code(user.mfa_secret, mfa_code):
            logger.warning("mfa_code_invalid", user_id=user_id_str)
            raise UnauthorizedError("Invalid MFA code")

        # Issue tokens
        tokens = await self._issue_tokens(user_id_str, ip_address, user_agent)

        # Update login info
        await self._user_repo.update_login_info(user.id)

        event = UserLoggedInEvent(
            user_id=user.id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info("mfa_login_completed", event_type=event.event_type, user_id=user_id_str)

        return {
            "requires_mfa": False,
            "user": {
                "id": user_id_str,
                "email": user.email,
                "role": user.role,
                "mfa_enabled": user.mfa_enabled,
            },
            "tokens": tokens.to_dict(),
        }

    async def _issue_tokens(
        self,
        user_id_str: str,
        ip_address: str,
        user_agent: str,
    ) -> TokenPair:
        """Generate token pair and create session."""
        access_token = JWTService.create_access_token(user_id_str)
        refresh_token = JWTService.create_refresh_token(user_id_str)

        refresh_payload = JWTService.decode_token(refresh_token)
        jti = refresh_payload["jti"] if refresh_payload else str(uuid.uuid4())

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
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._session_repo.create(
            user_id=uuid.UUID(user_id_str),
            refresh_token_jti=jti,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
