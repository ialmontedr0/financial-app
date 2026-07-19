import pytest
from httpx import AsyncClient

from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher


@pytest.mark.api
class TestLogin:
    """Tests for POST /auth/login."""

    async def _create_test_user(
        self, db_session, email: str = "login@test.com", password: str = "TestPass123!"
    ):
        """Helper to create a test user directly in DB."""
        user_repo = UserRepository(db_session)
        hashed = PasswordHasher.hash_password(password)
        user = await user_repo.create(email=email, password_hash=hashed)
        await db_session.commit()
        return user

    async def test_login_success(self, client: AsyncClient, db_session, test_password: str):
        email = "loginsuccess@test.com"
        await self._create_test_user(db_session, email, test_password)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["requires_mfa"] is False
        assert "tokens" in data
        assert "user" in data
        assert data["user"]["email"] == email

    async def test_login_wrong_password(self, client: AsyncClient, db_session, test_password: str):
        email = "wrongpwd@test.com"
        await self._create_test_user(db_session, email, test_password)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword123!"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "SomePass123!"},
        )
        assert response.status_code == 401

    async def test_login_invalid_payload(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "bad"},
        )
        assert response.status_code == 422
