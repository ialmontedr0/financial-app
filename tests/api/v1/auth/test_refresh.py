import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestRefreshToken:
    """Tests for POST /auth/refresh."""

    async def test_refresh_success(self, client: AsyncClient, test_password: str):
        email = "refresh@test.com"
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": test_password},
        )
        # Login to get real tokens with session in Redis
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )
        refresh_token = login_resp.json()["tokens"]["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]

    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_refresh_access_token_rejected(
        self, client: AsyncClient, valid_access_token: str
    ):
        """An access token should not work as refresh token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": valid_access_token},
        )
        assert response.status_code == 401
