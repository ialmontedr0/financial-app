"""Repository for user preferences persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from app.infrastructure.models.user_preference import UserPreferenceModel

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class UserPreferenceRepository:
    """Repository for UserPreferenceModel operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserPreferenceModel | None:
        """Get preferences by user ID."""
        stmt = select(UserPreferenceModel).where(UserPreferenceModel.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        **kwargs: str | bool,
    ) -> UserPreferenceModel:
        """Create default preferences for a user."""
        prefs = UserPreferenceModel(user_id=user_id, **kwargs)
        self._session.add(prefs)
        await self._session.flush()
        logger.info("preferences_created", user_id=str(user_id))
        return prefs

    async def get_or_create(self, user_id: uuid.UUID) -> UserPreferenceModel:
        """Get existing preferences or create defaults."""
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            prefs = await self.create(user_id)
        return prefs

    async def update(
        self,
        user_id: uuid.UUID,
        **kwargs: str | bool,
    ) -> UserPreferenceModel | None:
        """Update preference fields by user ID."""
        prefs = await self.get_by_user_id(user_id)
        if prefs is None:
            return None
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        await self._session.flush()
        await self._session.refresh(prefs)
        logger.info(
            "preferences_updated",
            user_id=str(user_id),
            fields=list(kwargs.keys()),
        )
        return prefs
