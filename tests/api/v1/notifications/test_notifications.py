"""Phase 18 Notification API tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestNotificationsAPI:
    async def _register_and_login(
        self, client: AsyncClient, email: str, password: str
    ) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_notification(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(
            client, "notif_create@test.com", test_password
        )
        resp = await client.post(
            "/api/v1/notifications/",
            json={
                "type": "transaction_alert",
                "title": "Nueva transaccion",
                "body": "Se detecto una transaccion de $1,500.00",
                "channels": ["push"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["success"] is True

    async def test_list_notifications(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(
            client, "notif_list@test.com", test_password
        )
        resp = await client.get(
            "/api/v1/notifications/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "notifications" in data
        assert "total" in data

    async def test_list_notifications_with_filters(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(
            client, "notif_filter@test.com", test_password
        )
        resp = await client.get(
            "/api/v1/notifications/?channel=push&is_read=false",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_get_notification_not_found(
        self, client: AsyncClient, test_password: str
    ):
        from uuid import uuid4

        token = await self._register_and_login(
            client, "notif_404@test.com", test_password
        )
        fake_id = str(uuid4())
        resp = await client.get(
            f"/api/v1/notifications/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_mark_read_not_found(self, client: AsyncClient, test_password: str):
        from uuid import uuid4

        token = await self._register_and_login(
            client, "notif_read@test.com", test_password
        )
        fake_id = str(uuid4())
        resp = await client.patch(
            f"/api/v1/notifications/{fake_id}/read",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_delete_notification_not_found(
        self, client: AsyncClient, test_password: str
    ):
        from uuid import uuid4

        token = await self._register_and_login(
            client, "notif_del@test.com", test_password
        )
        fake_id = str(uuid4())
        resp = await client.delete(
            f"/api/v1/notifications/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    async def test_get_preferences(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(
            client, "notif_prefs@test.com", test_password
        )
        resp = await client.get(
            "/api/v1/notifications/preferences/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "email_enabled" in data
        assert "push_enabled" in data

    async def test_update_preferences(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(
            client, "notif_upref@test.com", test_password
        )
        resp = await client.put(
            "/api/v1/notifications/preferences/",
            json={
                "email_enabled": True,
                "push_enabled": False,
                "telegram_enabled": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email_enabled"] is True
        assert data["push_enabled"] is False

    async def test_send_test_notification(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(
            client, "notif_test@test.com", test_password
        )
        resp = await client.post(
            "/api/v1/notifications/test",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    async def test_get_stats(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(
            client, "notif_stats@test.com", test_password
        )
        resp = await client.get(
            "/api/v1/notifications/stats/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "unread" in data
        assert "by_channel" in data

    async def test_bulk_mark_read(self, client: AsyncClient, test_password: str):
        from uuid import uuid4

        token = await self._register_and_login(
            client, "notif_bulk@test.com", test_password
        )
        resp = await client.post(
            "/api/v1/notifications/bulk-read",
            json={"notification_ids": [str(uuid4()), str(uuid4())]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "count" in data

    async def test_unauthorized_access(self, client: AsyncClient):
        resp = await client.get("/api/v1/notifications/")
        assert resp.status_code in (401, 403, 422)
