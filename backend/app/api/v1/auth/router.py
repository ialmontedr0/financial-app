import uuid

import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_user, get_db
from app.api.v1.auth.schemas import (
    DisableMFARequest,
    EnableMFAResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    MFAVerifyRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    RequestEmailVerificationRequest,
    RequestPasswordResetRequest,
    ResetPasswordRequest,
    UserResponse,
    VerifyEmailResponse,
)
from app.application.auth.disable_mfa import DisableMFAUseCase
from app.application.auth.enable_mfa import EnableMFAUseCase
from app.application.auth.get_current_user import GetCurrentUserUseCase
from app.application.auth.login_user import LoginUserUseCase
from app.application.auth.logout_user import LogoutUserUseCase
from app.application.auth.refresh_token import RefreshTokenUseCase
from app.application.auth.register_user import RegisterUserUseCase
from app.application.auth.request_email_verification import RequestEmailVerificationUseCase
from app.application.auth.request_password_reset import RequestPasswordResetUseCase
from app.application.auth.reset_password import ResetPasswordUseCase
from app.application.auth.verify_email import VerifyEmailUseCase

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _extract_device_info(request: Request) -> tuple[str, str]:
    """Extract IP address and user agent from the request."""
    ip_address = request.client.host if request.client else "0.0.0.0"  # noqa: S104
    user_agent = request.headers.get("user-agent", "unknown")
    return ip_address, user_agent


def _extract_refresh_jti(refresh_token: str | None) -> str | None:
    """Extract JTI from refresh token if provided."""
    if not refresh_token:
        return None
    from app.infrastructure.security.jwt_service import JWTService

    payload = JWTService.decode_token(refresh_token)
    if payload:
        return payload.get("jti")
    return None


# ============================================================
# POST /auth/register
# ============================================================
@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Register a new user",
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Register a new user account.

    - **email**: Valid email address
    - **password**: Minimum 8 characters

    Returns user data and JWT token pair.
    """
    ip_address, user_agent = _extract_device_info(request)

    use_case = RegisterUserUseCase(db)
    result = await use_case.execute(
        email=body.email,
        password=body.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return result


# ============================================================
# POST /auth/login
# ============================================================
@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login with email and password",
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate with email and password.

    If MFA is enabled, returns `requires_mfa: true` with a
    temporary `mfa_token`. Call `/auth/mfa/verify` to complete.
    """
    ip_address, user_agent = _extract_device_info(request)

    use_case = LoginUserUseCase(db)
    return await use_case.execute(
        email=body.email,
        password=body.password,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ============================================================
# POST /auth/mfa/verify
# ============================================================
@router.post(
    "/mfa/verify",
    response_model=LoginResponse,
    summary="Complete MFA verification during login",
)
async def verify_mfa(
    body: MFAVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Complete login by verifying the TOTP MFA code.

    - **mfa_token**: The temporary token from the login response
    - **code**: 6-digit code from authenticator app
    """
    ip_address, user_agent = _extract_device_info(request)

    use_case = LoginUserUseCase(db)
    return await use_case.complete_mfa_login(
        mfa_token=body.mfa_token,
        mfa_code=body.code,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ============================================================
# POST /auth/refresh
# ============================================================
@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access token",
)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh an access token using a valid refresh token.

    Implements token rotation: the old refresh token is invalidated
    and a new pair is issued. If reuse is detected, all sessions
    for the user are revoked.
    """
    ip_address, user_agent = _extract_device_info(request)

    use_case = RefreshTokenUseCase(db)
    return await use_case.execute(
        refresh_token=body.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
    )


# ============================================================
# POST /auth/logout
# ============================================================
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout current session",
)
async def logout(
    body: LogoutRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Logout the current session.

    Optionally pass `refresh_token` to revoke a specific session.
    """
    use_case = LogoutUserUseCase(db)

    if body.refresh_token:
        jti = _extract_refresh_jti(body.refresh_token)
        if jti:
            await use_case.execute_logout(jti)
    else:
        # Without a specific token, we can't revoke a specific session
        # The client should pass the refresh_token
        pass

    return {"message": "Logged out successfully"}


# ============================================================
# POST /auth/logout-all
# ============================================================
@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout all sessions",
)
async def logout_all(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke ALL sessions for the current user.

    This will force re-authentication on all devices.
    """
    user_id = uuid.UUID(current_user["sub"])

    use_case = LogoutUserUseCase(db)
    count = await use_case.execute_logout_all(user_id)

    return {"message": f"All sessions revoked ({count} sessions)"}


# ============================================================
# GET /auth/verify-email
# ============================================================
@router.get(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verify email address",
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Verify email address using the token sent via email.

    The token is passed as a query parameter.
    """
    use_case = VerifyEmailUseCase(db)
    return await use_case.execute(token=token)


# ============================================================
# POST /auth/request-email-verification
# ============================================================
@router.post(
    "/request-email-verification",
    response_model=MessageResponse,
    summary="Request new email verification",
)
async def request_email_verification(
    body: RequestEmailVerificationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Request a new email verification link.

    Always returns success message to prevent email enumeration.
    """
    use_case = RequestEmailVerificationUseCase(db)
    return await use_case.execute(email=body.email)


# ============================================================
# POST /auth/request-password-reset
# ============================================================
@router.post(
    "/request-password-reset",
    response_model=MessageResponse,
    summary="Request password reset",
)
async def request_password_reset(
    body: RequestPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Request a password reset link.

    Always returns success message to prevent email enumeration.
    """
    use_case = RequestPasswordResetUseCase(db)
    return await use_case.execute(email=body.email)


# ============================================================
# POST /auth/reset-password
# ============================================================
@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with token",
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset password using a valid reset token.

    After reset, all existing sessions are revoked.
    """
    use_case = ResetPasswordUseCase(db)
    return await use_case.execute(
        token=body.token,
        new_password=body.new_password,
    )


# ============================================================
# POST /auth/mfa/enable
# ============================================================
@router.post(
    "/mfa/enable",
    response_model=EnableMFAResponse,
    summary="Enable MFA",
)
async def enable_mfa(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Enable MFA for the current user.

    Returns a QR code (base64) and a secret key.
    Scan the QR with an authenticator app (Google Authenticator, Authy, etc.)
    then verify with a code to complete setup.
    """
    user_id = uuid.UUID(current_user["sub"])

    use_case = EnableMFAUseCase(db)
    return await use_case.execute(user_id=user_id)


# ============================================================
# POST /auth/mfa/disable
# ============================================================
@router.post(
    "/mfa/disable",
    response_model=MessageResponse,
    summary="Disable MFA",
)
async def disable_mfa(
    body: DisableMFARequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Disable MFA for the current user.

    Requires a valid TOTP code to confirm.
    """
    user_id = uuid.UUID(current_user["sub"])

    use_case = DisableMFAUseCase(db)
    return await use_case.execute(user_id=user_id, code=body.code)


# ============================================================
# GET /auth/me
# ============================================================
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the authenticated user's profile."""
    user_id = uuid.UUID(current_user["sub"])

    use_case = GetCurrentUserUseCase(db)
    return await use_case.execute(user_id=user_id)


# ============================================================
# GET /auth/sessions
# ============================================================
@router.get(
    "/sessions",
    response_model=list[dict],
    summary="List active sessions",
)
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all active sessions for the current user."""
    from app.infrastructure.repositories.session_repository import SessionRepository

    user_id = uuid.UUID(current_user["sub"])
    session_repo = SessionRepository(db)
    sessions = await session_repo.get_active_sessions(user_id)

    return [
        {
            "id": str(s.id),
            "device_info": s.device_info,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        }
        for s in sessions
    ]
