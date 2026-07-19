import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import UserModel

logger = structlog.get_logger()


class UserRepository:
    """Repository for user persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        email: str,
        password_hash: str,
        role: str = "user",
    ) -> UserModel:
        """Create a new user."""
        user = UserModel(
            email=email,
            password_hash=password_hash,
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        logger.info("user_created", user_id=str(user.id), email=email)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        """Get a user by ID (excluding soft-deleted)."""
        stmt = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        """Get a user by email (excluding soft-deleted)."""
        stmt = select(UserModel).where(
            UserModel.email == email.lower().strip(),
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, user_id: uuid.UUID, **kwargs) -> UserModel | None:
        """Update user fields by ID."""
        stmt = (
            update(UserModel).where(UserModel.id == user_id).values(**kwargs).returning(UserModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, user_id: uuid.UUID) -> None:
        """Soft-delete a user by setting deleted_at."""
        await self.update(user_id, deleted_at=datetime.now(UTC))

    async def verify_email(self, user_id: uuid.UUID) -> None:
        """Mark user email as verified."""
        await self.update(user_id, is_verified=True)

    async def update_mfa_secret(self, user_id: uuid.UUID, secret: str) -> None:
        """Enable MFA and store the secret."""
        await self.update(user_id, mfa_enabled=True, mfa_secret=secret)

    async def disable_mfa(self, user_id: uuid.UUID) -> None:
        """Disable MFA for a user."""
        await self.update(user_id, mfa_enabled=False, mfa_secret=None)

    async def update_login_info(self, user_id: uuid.UUID) -> None:
        """Update last_login_at and increment login_count."""

        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                last_login_at=datetime.now(UTC),
                login_count=UserModel.login_count + 1,
            )
        )
        await self._session.execute(stmt)

    async def update_password(self, user_id: uuid.UUID, password_hash: str) -> None:
        """Update the user password hash."""
        await self.update(user_id, password_hash=password_hash)
