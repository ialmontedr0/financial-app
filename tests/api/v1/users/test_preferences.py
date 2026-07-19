"""Tests for user preferences endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestUserPreferences:
    """Tests for GET/PATCH /users/me/preferences."""

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

    async def test_get_default_preferences(self, client: AsyncClient, test_password: str):
        email = "defaultprefs@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.get(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["currency_code"] == "DOP"
        assert data["timezone"] == "America/Santo_Domingo"
        assert data["language"] == "es"
        assert data["theme"] == "system"
        assert data["email_notifications"] is True

    async def test_update_preferences(self, client: AsyncClient, test_password: str):
        email = "updateprefs@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.patch(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "currency_code": "USD",
                "timezone": "America/New_York",
                "language": "en",
                "theme": "dark",
            },
        )
        assert response.status_code == 200

        # Verify update
        get_resp = await client.get(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = get_resp.json()
        assert data["currency_code"] == "USD"
        assert data["timezone"] == "America/New_York"
        assert data["language"] == "en"
        assert data["theme"] == "dark"
        # Defaults should remain
        assert data["email_notifications"] is True

    async def test_update_invalid_currency(self, client: AsyncClient, test_password: str):
        email = "invalidcurr@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.patch(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"currency_code": "XYZ"},
        )
        assert response.status_code == 422

    async def test_update_invalid_timezone(self, client: AsyncClient, test_password: str):
        email = "invalidtz@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.patch(
            "/api/v1/users/me/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json={"timezone": "Invalid/Zone"},
        )
        assert response.status_code == 422

    async def test_get_supported_values(self, client: AsyncClient):
        response = await client.get("/api/v1/users/supported-values")
        assert response.status_code == 200
        data = response.json()
        assert len(data["currencies"]) > 0
        assert len(data["timezones"]) > 0
        assert len(data["languages"]) > 0
        # Check DOP is included
        currency_codes = [c["code"] for c in data["currencies"]]
        assert "DOP" in currency_codes
