"""Tests for user profile endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestUserProfile:
    """Tests for GET/PATCH /users/me."""

    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        """Helper: register user, login, return access token."""
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_get_profile(self, client: AsyncClient, test_password: str):
        email = "profile@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert "profile" in data
        assert data["profile"]["first_name"] is None  # Not set yet

    async def test_update_profile(self, client: AsyncClient, test_password: str):
        email = "updateprofile@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "Tony",
                "last_name": "Montana",
                "city": "Santo Domingo",
                "country_code": "DO",
            },
        )
        assert response.status_code == 200

        # Verify update
        get_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = get_resp.json()
        assert data["profile"]["first_name"] == "Tony"
        assert data["profile"]["last_name"] == "Montana"
        assert data["profile"]["city"] == "Santo Domingo"
        assert data["profile"]["country_code"] == "DO"

    async def test_update_profile_invalid_country(self, client: AsyncClient, test_password: str):
        email = "invalidcountry@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"country_code": "INVALID"},
        )
        assert response.status_code == 422

    async def test_get_profile_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 422  # Missing Authorization header
