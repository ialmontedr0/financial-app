"""Pydantic schemas for Users API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================
# User Profile Response
# ============================================================
class ProfileData(BaseModel):
    """Extended profile data."""

    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    date_of_birth: str | None = None
    gender: str | None = None
    bio: str | None = None
    phone_secondary: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state_province: str | None = None
    country_code: str | None = None
    postal_code: str | None = None


class UserProfileResponse(BaseModel):
    """Full user profile response."""

    id: str
    email: str
    role: str
    phone: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    is_verified: bool = False
    mfa_enabled: bool = False
    last_login_at: str | None = None
    login_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    profile: ProfileData = Field(default_factory=ProfileData)


# ============================================================
# Update Profile Request
# ============================================================
class UpdateProfileRequest(BaseModel):
    """Request to update user profile (all fields optional)."""

    # User-level fields
    phone: str | None = Field(None, max_length=50, description="Primary phone number")
    avatar_url: str | None = Field(None, max_length=500, description="Avatar URL")

    # Profile fields
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    display_name: str | None = Field(None, max_length=200)
    date_of_birth: str | None = Field(None, description="Format: YYYY-MM-DD")
    gender: str | None = Field(None, description="male, female, other, prefer_not_to_say")
    bio: str | None = Field(None, max_length=500)
    phone_secondary: str | None = Field(None, max_length=50)
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state_province: str | None = Field(None, max_length=100)
    country_code: str | None = Field(None, max_length=2, description="ISO 3166-1 alpha-2")
    postal_code: str | None = Field(None, max_length=20)


class UpdateProfileResponse(BaseModel):
    """Updated profile response."""

    message: str = "Profile updated successfully"


# ============================================================
# User Preferences Response
# ============================================================
class UserPreferencesResponse(BaseModel):
    """User preferences response."""

    currency_code: str = "DOP"
    timezone: str = "America/Santo_Domingo"
    language: str = "es"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "24h"
    number_format: str = "#,##0.00"
    first_day_of_week: str = "monday"
    theme: str = "system"
    email_notifications: bool = True
    push_notifications: bool = True
    marketing_emails: bool = False
    updated_at: str | None = None


# ============================================================
# Update Preferences Request
# ============================================================
class UpdatePreferencesRequest(BaseModel):
    """Request to update user preferences (all fields optional)."""

    currency_code: str | None = Field(None, max_length=3, description="ISO 4217 currency code")
    timezone: str | None = Field(None, max_length=50, description="IANA timezone")
    language: str | None = Field(None, max_length=5, description="ISO 639-1 language code")
    date_format: str | None = Field(
        None, max_length=20, description="DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD"
    )
    time_format: str | None = Field(None, description="12h or 24h")
    number_format: str | None = Field(None, max_length=30)
    first_day_of_week: str | None = Field(None, description="monday or sunday")
    theme: str | None = Field(None, description="light, dark, or system")
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    marketing_emails: bool | None = None


class UpdatePreferencesResponse(BaseModel):
    """Updated preferences response."""

    message: str = "Preferences updated successfully"


# ============================================================
# Delete Account
# ============================================================
class DeleteAccountRequest(BaseModel):
    """Confirm account deletion."""

    confirm: bool = Field(..., description="Must be true to confirm deletion")


class DeleteAccountResponse(BaseModel):
    """Account deletion response."""

    message: str
    sessions_revoked: int = 0


# ============================================================
# Supported Values Response (for frontend dropdowns)
# ============================================================
class CurrencyOption(BaseModel):
    code: str
    name: str


class TimezoneOption(BaseModel):
    timezone: str
    name: str


class LanguageOption(BaseModel):
    code: str
    name: str


class SupportedValuesResponse(BaseModel):
    """List of supported currencies, timezones, languages."""

    currencies: list[CurrencyOption]
    timezones: list[TimezoneOption]
    languages: list[LanguageOption]
