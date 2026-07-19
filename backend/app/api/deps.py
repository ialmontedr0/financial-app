import uuid
from collections.abc import AsyncGenerator

import structlog
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_async_session
from app.infrastructure.security.jwt_service import JWTService

logger = structlog.get_logger()


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Database session dependency for FastAPI."""
    async for session in get_async_session():
        yield session


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate the current user from the Authorization header.

    Returns the decoded JWT payload containing user_id in 'sub'.
    """
    from app.middleware.error_handler import UnauthorizedError

    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header format")

    token = authorization.replace("Bearer ", "")
    payload = JWTService.verify_token(token, expected_type="access")

    if payload is None:
        raise UnauthorizedError("Invalid or expired access token")

    # Check for MFA pending tokens — they should not access protected routes
    if payload.get("mfa_pending"):
        raise UnauthorizedError("MFA verification required")

    return payload


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Ensure the current user is active and verified."""
    from app.infrastructure.repositories.user_repository import UserRepository
    from app.middleware.error_handler import ForbiddenError, UnauthorizedError

    user_id = uuid.UUID(current_user["sub"])
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise UnauthorizedError("User not found")

    if not user.is_active:
        raise ForbiddenError("Account is deactivated")

    return current_user


async def get_current_verified_user(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Ensure the current user is verified."""
    from app.infrastructure.repositories.user_repository import UserRepository
    from app.middleware.error_handler import ForbiddenError

    user_id = uuid.UUID(current_user["sub"])
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user and not user.is_verified:
        raise ForbiddenError("Email not verified")

    return current_user
