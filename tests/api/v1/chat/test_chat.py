"""API tests for the chat module."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestChatSessions:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return login.json()["tokens"]["access_token"]

    async def test_create_and_list_session(self, client: AsyncClient, test_password: str):
        email = "chat1@test.com"
        token = await self._register_and_login(client, email, test_password)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(
            "/api/v1/chat/sessions",
            headers=headers,
            json={"title": "Mi chat", "chat_type": "finance"},
        )
        assert resp.status_code == 201
        session_id = resp.json()["id"]
        assert resp.json()["title"] == "Mi chat"

        resp = await client.get("/api/v1/chat/sessions", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        resp = await client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["messages"] == []

    async def test_delete_session(self, client: AsyncClient, test_password: str):
        email = "chat2@test.com"
        token = await self._register_and_login(client, email, test_password)
        headers = {"Authorization": f"Bearer {token}"}

        created = await client.post("/api/v1/chat/sessions", headers=headers, json={})
        session_id = created.json()["id"]

        resp = await client.delete(f"/api/v1/chat/sessions/{session_id}", headers=headers)
        assert resp.status_code == 200

        resp = await client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
        assert resp.status_code == 404

    async def test_send_message_streams(self, client: AsyncClient, test_password: str):
        email = "chat3@test.com"
        token = await self._register_and_login(client, email, test_password)
        headers = {"Authorization": f"Bearer {token}"}

        created = await client.post("/api/v1/chat/sessions", headers=headers, json={})
        session_id = created.json()["id"]

        resp = await client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            headers=headers,
            json={"content": "hola"},
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        session = await client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
        roles = [m["role"] for m in session.json()["messages"]]
        assert "user" in roles
        assert "assistant" in roles
