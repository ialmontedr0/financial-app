"""Repository for user profile persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from app.infrastructure.models.user_profile import UserProfileModel

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UserProfileRepository:
    """Repository for UserProfileModel operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserProfileModel | None:
        """Get profile by user ID."""
        stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        **kwargs: str | None,
    ) -> UserProfileModel:
        """Create a new profile for a user."""
        profile = UserProfileModel(user_id=user_id, **kwargs)
        self._session.add(profile)
        await self._session.flush()
        logger.info("profile_created", user_id=str(user_id))
        return profile

    async def get_or_create(self, user_id: uuid.UUID) -> UserProfileModel:
        """Get existing profile or create an empty one."""
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            profile = await self.create(user_id)
        return profile

    async def update(
        self,
        user_id: uuid.UUID,
        **kwargs: str | None,
    ) -> UserProfileModel | None:
        """Update profile fields by user ID."""
        profile = await self.get_by_user_id(user_id)
        if profile is None:
            return None
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self._session.flush()
        logger.info("profile_updated", user_id=str(user_id), fields=list(kwargs.keys()))
        return profile
