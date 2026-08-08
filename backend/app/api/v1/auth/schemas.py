from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.validators import validate_password_strength


# ============================================================
# Register
# ============================================================
class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 characters)",
    )

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserResponse(BaseModel):
    """Public user data."""

    id: str
    email: str
    role: str = "user"
    phone: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    is_verified: bool = False
    mfa_enabled: bool = False
    login_count: int = 0
    last_login_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class TokenResponse(BaseModel):
    """JWT token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class RegisterResponse(BaseModel):
    """Registration response."""

    user: UserResponse
    tokens: TokenResponse


# ============================================================
# Login
# ============================================================
class LoginRequest(BaseModel):
    """Schema for login."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response. May require MFA."""

    requires_mfa: bool = False
    mfa_token: str | None = None
    message: str | None = None
    user: UserResponse | None = None
    tokens: TokenResponse | None = None


# ============================================================
# MFA
# ============================================================
class MFAVerifyRequest(BaseModel):
    """MFA verification during login."""

    mfa_token: str = Field(..., description="Temporary MFA token from login")
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code",
    )


class EnableMFAResponse(BaseModel):
    """MFA enablement response with QR code."""

    secret: str
    qr_code_base64: str
    message: str


class ConfirmMFARequest(BaseModel):
    """Confirm MFA setup with a TOTP code."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code to verify before enabling MFA",
    )


class DisableMFARequest(BaseModel):
    """Disable MFA request."""

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="Current 6-digit TOTP code to verify",
    )


# ============================================================
# Refresh
# ============================================================
class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class RefreshResponse(BaseModel):
    """Token refresh response."""

    tokens: TokenResponse


# ============================================================
# Logout
# ============================================================
class LogoutRequest(BaseModel):
    """Logout request (optional refresh_token for specific session)."""

    refresh_token: str | None = None


class RevokeSessionRequest(BaseModel):
    """Revoke a single session by id."""

    session_id: str


# ============================================================
# Email Verification
# ============================================================
class VerifyEmailRequest(BaseModel):
    """Email verification request."""

    token: str


class VerifyEmailResponse(BaseModel):
    """Email verification response."""

    message: str


class RequestEmailVerificationRequest(BaseModel):
    """Request new email verification."""

    email: EmailStr


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


# ============================================================
# Password Reset
# ============================================================
class RequestPasswordResetRequest(BaseModel):
    """Request password reset."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""

    token: str
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


# ============================================================
# Sessions
# ============================================================
class SessionResponse(BaseModel):
    """Active session info."""

    jti: str | None = None
    device_info: str = ""
    ip_address: str = ""
    created_at: str | None = None
    is_active: bool = True
