"""Use case: Update user profile fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.infrastructure.repositories.user_profile_repository import UserProfileRepository
from app.infrastructure.repositories.user_repository import UserRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Fields that belong to the user table (not profile)
USER_TABLE_FIELDS = {"phone", "avatar_url"}

# Fields that belong to the profile table
PROFILE_TABLE_FIELDS = {
    "first_name",
    "last_name",
    "display_name",
    "date_of_birth",
    "gender",
    "bio",
    "phone_secondary",
    "address_line1",
    "address_line2",
    "city",
    "state_province",
    "country_code",
    "postal_code",
}


class UpdateUserProfileUseCase:
    """Update user profile and/or user-level fields."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._profile_repo = UserProfileRepository(session)

    async def execute(self, user_id: uuid.UUID, **fields: Any) -> dict:
        """Update profile fields. Accepts any combination of profile fields."""
        from app.middleware.error_handler import NotFoundError, ValidationError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User")

        # Split fields between user table and profile table
        user_fields: dict[str, Any] = {}
        profile_fields: dict[str, Any] = {}

        for key, value in fields.items():
            if key in USER_TABLE_FIELDS:
                user_fields[key] = value
            elif key in PROFILE_TABLE_FIELDS:
                profile_fields[key] = value
            else:
                raise ValidationError(f"Unknown field: {key}")

        # Validate country_code if provided
        if "country_code" in profile_fields and profile_fields["country_code"] is not None:
            from app.domain.users.value_objects import CountryCode

            try:
                CountryCode(profile_fields["country_code"])
            except ValueError as e:
                raise ValidationError(str(e))  # noqa: B904

        # Update user table fields
        if user_fields:
            await self._user_repo.update(user_id, **user_fields)

        # Update profile fields (auto-create if missing)
        if profile_fields:
            await self._profile_repo.get_or_create(user_id)
            await self._profile_repo.update(user_id, **profile_fields)

        # Return updated data
        from app.application.users.get_user_profile import GetUserProfileUseCase

        get_use_case = GetUserProfileUseCase(self._session)
        return await get_use_case.execute(user_id)
