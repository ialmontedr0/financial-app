import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestSessions:
    """Tests for session listing and revocation."""

    async def _register_and_login(self, client: AsyncClient, test_password: str, email: str):
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": test_password},
        )
        return await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": test_password},
        )

    async def test_list_sessions(self, client: AsyncClient, test_password: str):
        email = "sessions@test.com"
        login_resp = await self._register_and_login(client, test_password, email)
        assert login_resp.status_code == 200
        access_token = login_resp.json()["tokens"]["access_token"]

        response = await client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert data["total"] >= 1
        session = data["sessions"][0]
        assert "id" in session
        assert "device_type" in session
        assert "last_active_at" in session

    async def test_revoke_session(self, client: AsyncClient, test_password: str):
        email = "revoke@test.com"
        # Two concurrent logins => two active sessions.
        await self._register_and_login(client, test_password, email)
        login2 = await self._register_and_login(client, test_password, email)
        assert login2.status_code == 200
        access_token = login2.json()["tokens"]["access_token"]

        sessions_resp = await client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        sessions = sessions_resp.json()["sessions"]
        assert len(sessions) >= 2
        total_before = sessions_resp.json()["total"]
        session_id = sessions[0]["id"]

        revoke_resp = await client.post(
            "/api/v1/auth/sessions/revoke",
            json={"session_id": session_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert revoke_resp.status_code == 200
        assert "message" in revoke_resp.json()

        after = await client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert after.json()["total"] == total_before - 1

    async def test_revoke_non_existent_session(self, client: AsyncClient, test_password: str):
        email = "revoke404@test.com"
        login_resp = await self._register_and_login(client, test_password, email)
        access_token = login_resp.json()["tokens"]["access_token"]

        response = await client.post(
            "/api/v1/auth/sessions/revoke",
            json={"session_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 404