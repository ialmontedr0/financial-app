"""Tests for access token blacklist on logout."""

import pytest
from httpx import AsyncClient

from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.token_blacklist_service import TokenBlacklistService


@pytest.mark.api
class TestTokenBlacklist:
    """Logout must revoke the access token immediately."""

    async def test_access_token_rejected_after_logout(
        self, client: AsyncClient, test_password: str
    ):
        email = "blacklist@test.com"
        await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": test_password}
        )
        tokens = login.json()["tokens"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # Token works before logout
        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200

        # Logout with the refresh token
        logout = await client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json={"refresh_token": refresh_token},
        )
        assert logout.status_code == 200

        # Access token must now be rejected
        me_after = await client.get("/api/v1/auth/me", headers=headers)
        assert me_after.status_code == 401
        assert me_after.json()["error"]["message"] == "Token has been revoked"

    async def test_logout_all_revokes_access_token(self, client: AsyncClient, test_password: str):
        email = "blacklistall@test.com"
        await client.post("/api/v1/auth/register", json={"email": email, "password": test_password})
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": test_password}
        )
        access_token = login.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 200

        resp = await client.post("/api/v1/auth/logout-all", headers=headers)
        assert resp.status_code == 200

        assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401

    async def test_service_blacklists_directly(self, client: AsyncClient):
        """A token blacklisted directly is rejected by protected routes."""
        token = JWTService.create_access_token("00000000-0000-0000-0000-000000000001")
        await TokenBlacklistService.blacklist_token(token)

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        assert response.json()["error"]["message"] == "Token has been revoked"
