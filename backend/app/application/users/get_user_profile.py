"""Use case: Get user profile with user info."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.user_profile_repository import UserProfileRepository
from app.infrastructure.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


logger = structlog.get_logger()


class GetUserProfileUseCase:
    """Get the authenticated user's full profile."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._profile_repo = UserProfileRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Return user info + extended profile."""
        from app.middleware.error_handler import NotFoundError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User")

        # Profile is auto-created if missing
        profile = await self._profile_repo.get_or_create(user_id)

        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "mfa_enabled": user.mfa_enabled,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "login_count": user.login_count,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "profile": {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "display_name": profile.display_name,
                "date_of_birth": profile.date_of_birth.isoformat()
                if profile.date_of_birth
                else None,
                "gender": profile.gender,
                "bio": profile.bio,
                "phone_secondary": profile.phone_secondary,
                "address_line1": profile.address_line1,
                "address_line2": profile.address_line2,
                "city": profile.city,
                "state_province": profile.state_province,
                "country_code": profile.country_code,
                "postal_code": profile.postal_code,
            },
        }
