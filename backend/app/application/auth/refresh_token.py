import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.auth.value_objects import TokenPair
from app.infrastructure.cache.session_store import SessionStore
from app.infrastructure.repositories.session_repository import SessionRepository
from app.infrastructure.security.jwt_service import JWTService

logger = structlog.get_logger()
settings = get_settings()


class RefreshTokenUseCase:
    """Refresh access token using a valid refresh token.

    Implements refresh token rotation: the old refresh token
    is invalidated and a new pair is issued.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._session_repo = SessionRepository(session)
        self._session_store = SessionStore()

    async def execute(
        self,
        refresh_token: str,
        ip_address: str = "0.0.0.0",  # noqa: S104
        user_agent: str = "unknown",
    ) -> dict:
        """Execute token refresh with rotation."""
        from app.middleware.error_handler import UnauthorizedError

        # Verify the refresh token
        payload = JWTService.verify_token(refresh_token, expected_type="refresh")
        if payload is None:
            raise UnauthorizedError("Invalid or expired refresh token")

        user_id = payload["sub"]
        old_jti = payload["jti"]

        # Check if the refresh token JTI exists in Redis
        stored_user_id = await self._session_store.get_refresh_token(old_jti)
        if stored_user_id is None:
            # Token reuse detected — revoke all sessions for this user
            logger.warning(
                "refresh_token_reuse_detected",
                user_id=user_id,
                jti=old_jti,
            )
            await self._revoke_all_sessions(user_id)
            raise UnauthorizedError("Refresh token has been reused. All sessions revoked.")

        # Invalidate old refresh token
        await self._session_store.delete_refresh_token(old_jti)
        await self._session_store.delete_session(old_jti)

        # Revoke old session in DB
        await self._session_repo.revoke(old_jti)

        # Issue new token pair
        new_access_token = JWTService.create_access_token(user_id)
        new_refresh_token = JWTService.create_refresh_token(user_id)

        new_payload = JWTService.decode_token(new_refresh_token)
        new_jti = new_payload["jti"] if new_payload else str(uuid.uuid4())

        # Store new session
        device_info = f"{user_agent[:50]}|{ip_address}"
        ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        await self._session_store.create_session(
            jti=new_jti,
            user_id=user_id,
            device_info=device_info,
            ip_address=ip_address,
            ttl_seconds=ttl_seconds,
        )
        await self._session_store.store_refresh_token(
            jti=new_jti,
            user_id=user_id,
            ttl_seconds=ttl_seconds,
        )

        # Store new session in DB
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self._session_repo.create(
            user_id=uuid.UUID(user_id),
            refresh_token_jti=new_jti,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )

        logger.info("token_refreshed", user_id=user_id, old_jti=old_jti, new_jti=new_jti)

        token_pair = TokenPair(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return {"tokens": token_pair.to_dict()}

    async def _revoke_all_sessions(self, user_id: str) -> None:
        """Revoke all sessions when token reuse is detected."""
        await self._session_store.revoke_all_user_sessions(user_id)
        await self._session_repo.revoke_all_for_user(uuid.UUID(user_id))
