"""Tests for login lockout after too many failed attempts."""

import pytest
from httpx import AsyncClient

from app.application.auth.lockout_service import LockoutService
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher


@pytest.mark.api
class TestLockout:
    """Account lockout must trigger after repeated failed logins."""

    async def _create_user(self, db_session, email: str, password: str = "TestPassword123!"):  # noqa: S107
        user_repo = UserRepository(db_session)
        hashed = PasswordHasher.hash_password(password)
        user = await user_repo.create(email=email, password_hash=hashed)
        await db_session.commit()
        return user

    async def test_locked_after_max_failed_attempts(
        self, client: AsyncClient, db_session, test_password: str
    ):
        email = "lockout1@test.com"
        await self._create_user(db_session, email)

        for _ in range(5):
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "WrongPassword123!"},
            )
            assert response.status_code == 401

        # Even with the correct password, the account is locked
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )
        assert response.status_code == 423
        assert response.json()["error"]["code"] == "TOO_MANY_ATTEMPTS"

    async def test_successful_login_resets_counter(
        self, client: AsyncClient, db_session, test_password: str
    ):
        email = "lockout2@test.com"
        user = await self._create_user(db_session, email)

        for _ in range(3):
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "WrongPassword123!"},
            )
            assert response.status_code == 401

        lockout_service = LockoutService(db_session)
        assert await lockout_service.is_locked(user.id) is False

        # Correct password logs in successfully and clears failures
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )
        assert response.status_code == 200

        assert await lockout_service.is_locked(user.id) is False

    async def test_lockout_cleared_after_reset(
        self, client: AsyncClient, db_session, test_password: str
    ):
        email = "lockout3@test.com"
        user = await self._create_user(db_session, email)

        for _ in range(5):
            await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "WrongPassword123!"},
            )

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )
        assert response.status_code == 423

        # Admin/service can unlock by resetting failed attempts
        lockout_service = LockoutService(db_session)
        await lockout_service.reset(user.id)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )
        assert response.status_code == 200
