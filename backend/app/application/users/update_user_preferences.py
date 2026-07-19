"""Use case: Update user preferences (full or partial)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.user_preference_repository import UserPreferenceRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Allowed preference fields
ALLOWED_PREFERENCE_FIELDS = {
    "currency_code",
    "timezone",
    "language",
    "date_format",
    "time_format",
    "number_format",
    "first_day_of_week",
    "theme",
    "email_notifications",
    "push_notifications",
    "marketing_emails",
}


class UpdateUserPreferencesUseCase:
    """Update user preferences (partial or full replacement)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._prefs_repo = UserPreferenceRepository(session)

    async def execute(self, user_id: uuid.UUID, **fields: Any) -> dict:
        """Update preference fields."""
        from app.middleware.error_handler import ValidationError

        # Validate fields
        invalid_fields = set(fields.keys()) - ALLOWED_PREFERENCE_FIELDS
        if invalid_fields:
            raise ValidationError(f"Unknown fields: {', '.join(invalid_fields)}")

        # Validate currency if provided
        if "currency_code" in fields and fields["currency_code"] is not None:
            from app.domain.users.value_objects import CurrencyCode

            try:
                CurrencyCode(fields["currency_code"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904
            fields["currency_code"] = fields["currency_code"].upper()

        # Validate timezone if provided
        if "timezone" in fields and fields["timezone"] is not None:
            from app.domain.users.value_objects import TimezoneCode

            try:
                TimezoneCode(fields["timezone"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904

        # Validate language if provided
        if "language" in fields and fields["language"] is not None:
            from app.domain.users.value_objects import LanguageCode

            try:
                LanguageCode(fields["language"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904

        # Validate enum fields
        if "time_format" in fields and fields["time_format"] not in ("12h", "24h"):
            raise ValidationError("time_format must be '12h' or '24h'")
        if "first_day_of_week" in fields and fields["first_day_of_week"] not in (
            "monday",
            "sunday",
        ):
            raise ValidationError("first_day_of_week must be 'monday' or 'sunday'")
        if "theme" in fields and fields["theme"] not in ("light", "dark", "system"):
            raise ValidationError("theme must be 'light', 'dark', or 'system'")

        # Ensure preferences exist
        await self._prefs_repo.get_or_create(user_id)

        # Update
        prefs = await self._prefs_repo.update(user_id, **fields)

        if prefs is None:
            from app.middleware.error_handler import NotFoundError

            raise NotFoundError("User preferences")

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
