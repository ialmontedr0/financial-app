"""Integration tests for the LockoutService."""

from datetime import UTC, datetime, timedelta

import pytest

from app.application.auth.lockout_service import LockoutService
from app.infrastructure.models.login_attempt import LoginAttemptModel
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher


@pytest.mark.integration
class TestLockoutService:
    """Service-level tests for failed-attempt counting and reset."""

    async def _create_user(self, db_session, email: str):
        user_repo = UserRepository(db_session)
        hashed = PasswordHasher.hash_password("TestPass123!")
        user = await user_repo.create(email=email, password_hash=hashed)
        await db_session.commit()
        return user

    async def test_not_locked_under_threshold(self, db_session):
        user = await self._create_user(db_session, "locksvc1@test.com")
        service = LockoutService(db_session)

        for _ in range(3):
            await service.record_failed_attempt(user.id, "127.0.0.1")

        assert await service.is_locked(user.id) is False

    async def test_locked_at_threshold(self, db_session):
        user = await self._create_user(db_session, "locksvc2@test.com")
        service = LockoutService(db_session)

        for _ in range(5):
            await service.record_failed_attempt(user.id, "127.0.0.1")

        assert await service.is_locked(user.id) is True

    async def test_reset_clears_lockout(self, db_session):
        user = await self._create_user(db_session, "locksvc3@test.com")
        service = LockoutService(db_session)

        for _ in range(5):
            await service.record_failed_attempt(user.id, "127.0.0.1")
        assert await service.is_locked(user.id) is True

        await service.reset(user.id)
        await db_session.commit()
        assert await service.is_locked(user.id) is False

    async def test_old_attempts_do_not_count(self, db_session):
        user = await self._create_user(db_session, "locksvc4@test.com")
        service = LockoutService(db_session)

        stale = LoginAttemptModel(
            user_id=user.id,
            ip_address="127.0.0.1",
            attempted_at=datetime.now(UTC) - timedelta(minutes=30),
            success=False,
        )
        db_session.add(stale)
        await db_session.commit()

        assert await service.is_locked(user.id) is False

    async def test_successful_attempt_recorded(self, db_session):
        user = await self._create_user(db_session, "locksvc5@test.com")
        service = LockoutService(db_session)

        await service.record_successful_attempt(user.id, "127.0.0.1")
        await db_session.flush()
        assert await service.is_locked(user.id) is False
