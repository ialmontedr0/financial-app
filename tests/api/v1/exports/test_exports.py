"""Export API tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestExports:
    async def _register_and_login(
        self, client: AsyncClient, email: str, password: str
    ) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login.json()["tokens"]["access_token"]

    async def test_export_csv(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "export_csv@test.com", test_password)
        resp = await client.get(
            "/api/v1/exports/transactions/csv",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    async def test_export_excel(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "export_xlsx@test.com", test_password)
        resp = await client.get(
            "/api/v1/exports/transactions/excel",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    async def test_export_pdf(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "export_pdf@test.com", test_password)
        resp = await client.get(
            "/api/v1/exports/transactions/pdf",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    async def test_export_goals_pdf(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "export_goals@test.com", test_password)
        resp = await client.get(
            "/api/v1/exports/goals/pdf",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    async def test_export_calendar(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "export_cal@test.com", test_password)
        resp = await client.get(
            "/api/v1/exports/calendar/recurring",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "text/calendar" in resp.headers["content-type"]
