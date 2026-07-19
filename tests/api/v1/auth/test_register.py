import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestRegister:
    """Tests for POST /auth/register."""

    async def test_register_success(self, client: AsyncClient, test_email: str, test_password: str):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "password": test_password},
        )
        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "tokens" in data
        assert data["user"]["email"] == test_email
        assert data["user"]["is_active"] is True
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert data["tokens"]["token_type"] == "bearer"

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_email: str, test_password: str
    ):
        # Register first user
        await client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "password": test_password},
        )
        # Try to register again
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "password": test_password},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    async def test_register_invalid_email(self, client: AsyncClient, test_password: str):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": test_password},
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient, test_email: str):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "password": "short"},
        )
        assert response.status_code == 422

    async def test_register_empty_body(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={},
        )
        assert response.status_code == 422
