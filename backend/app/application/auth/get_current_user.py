import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.user_repository import UserRepository

logger = structlog.get_logger()


class GetCurrentUserUseCase:
    """Get the current authenticated user's profile."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Return user profile data."""
        from app.middleware.error_handler import NotFoundError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User")

        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "mfa_enabled": user.mfa_enabled,
            "login_count": user.login_count,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
