"""Use case: Get user preferences."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.user_preference_repository import UserPreferenceRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetUserPreferencesUseCase:
    """Get the authenticated user's preferences."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._prefs_repo = UserPreferenceRepository(session)

    async def execute(self, user_id: uuid.UUID) -> dict:
        """Return user preferences (auto-created with defaults if missing)."""
        prefs = await self._prefs_repo.get_or_create(user_id)

        return {
            "currency_code": prefs.currency_code,
            "timezone": prefs.timezone,
            "language": prefs.language,
            "date_format": prefs.date_format,
            "time_format": prefs.time_format,
            "number_format": prefs.number_format,
            "first_day_of_week": prefs.first_day_of_week,
            "theme": prefs.theme,
            "email_notifications": prefs.email_notifications,
            "push_notifications": prefs.push_notifications,
            "marketing_emails": prefs.marketing_emails,
            "updated_at": prefs.updated_at.isoformat() if prefs.updated_at else None,
        }
