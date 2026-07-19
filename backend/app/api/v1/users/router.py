"""Users API router — Profile, Preferences, Account management."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.api.v1.users.schemas import (
    DeleteAccountRequest,
    DeleteAccountResponse,
    SupportedValuesResponse,
    UpdatePreferencesRequest,
    UpdatePreferencesResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
    UserPreferencesResponse,
    UserProfileResponse,
)
from app.application.users.delete_user_account import DeleteUserAccountUseCase
from app.application.users.get_user_preferences import GetUserPreferencesUseCase
from app.application.users.get_user_profile import GetUserProfileUseCase
from app.application.users.update_user_preferences import UpdateUserPreferencesUseCase
from app.application.users.update_user_profile import UpdateUserProfileUseCase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================
# Profile Endpoints
# ============================================================


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile including extended profile data.",
)
async def get_me(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the authenticated user's full profile."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetUserProfileUseCase(db)
    result = await use_case.execute(user_id)
    return result


@router.patch(
    "/me",
    response_model=UpdateProfileResponse,
    summary="Update current user profile",
    description="Update profile fields. Only provided fields are updated.",
)
async def update_me(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update the authenticated user's profile."""
    user_id = uuid.UUID(current_user["sub"])
    # Filter out None values (PATCH semantics)
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    use_case = UpdateUserProfileUseCase(db)
    await use_case.execute(user_id, **fields)
    return {"message": "Profile updated successfully"}


# ============================================================
# Preferences Endpoints
# ============================================================


@router.get(
    "/me/preferences",
    response_model=UserPreferencesResponse,
    summary="Get user preferences",
    description="Returns user preferences for currency, timezone, language, formatting, and notifications.",
)
async def get_my_preferences(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the authenticated user's preferences."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetUserPreferencesUseCase(db)
    result = await use_case.execute(user_id)
    return result


@router.patch(
    "/me/preferences",
    response_model=UpdatePreferencesResponse,
    summary="Update user preferences",
    description="Partial update of user preferences. Only provided fields are updated.",
)
async def update_my_preferences(
    body: UpdatePreferencesRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update the authenticated user's preferences (partial)."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    use_case = UpdateUserPreferencesUseCase(db)
    await use_case.execute(user_id, **fields)
    return {"message": "Preferences updated successfully"}


# ============================================================
# Account Management
# ============================================================


@router.delete(
    "/me",
    response_model=DeleteAccountResponse,
    summary="Delete current user account",
    description="Soft-deletes the user account and revokes all sessions. Requires confirmation.",
)
async def delete_me(
    body: DeleteAccountRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Soft-delete the authenticated user's account."""
    if not body.confirm:
        from app.middleware.error_handler import ValidationError

        raise ValidationError("Must set confirm=true to delete account")

    user_id = uuid.UUID(current_user["sub"])
    use_case = DeleteUserAccountUseCase(db)
    result = await use_case.execute(user_id)
    return result


# ============================================================
# Supported Values (for frontend dropdowns)
# ============================================================


@router.get(
    "/supported-values",
    response_model=SupportedValuesResponse,
    summary="Get supported currencies, timezones, languages",
    description="Returns all supported currencies, timezones, and languages for use in preference forms.",
)
async def get_supported_values() -> dict:
    """Return supported localization values."""
    from app.domain.users.value_objects import (
        SUPPORTED_CURRENCIES,
        SUPPORTED_LANGUAGES,
        SUPPORTED_TIMEZONES,
    )

    return {
        "currencies": [
            {"code": code, "name": name} for code, name in sorted(SUPPORTED_CURRENCIES.items())
        ],
        "timezones": [
            {"timezone": tz, "name": name} for tz, name in sorted(SUPPORTED_TIMEZONES.items())
        ],
        "languages": [
            {"code": code, "name": name} for code, name in sorted(SUPPORTED_LANGUAGES.items())
        ],
    }
