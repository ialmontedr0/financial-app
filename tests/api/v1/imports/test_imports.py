"""Import API tests."""

import io

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestImports:
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

    async def test_upload_csv(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "import_csv@test.com", test_password)
        csv_content = b"date,description,amount,type\n2024-01-15,Groceries,50.00,expense\n2024-01-16,Salary,3000.00,income"
        resp = await client.post(
            "/api/v1/imports/transactions",
            files={"file": ("transactions.csv", io.BytesIO(csv_content), "text/csv")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_rows"] == 2
        assert "job_id" in data

    async def test_upload_invalid_extension(
        self, client: AsyncClient, test_password: str
    ):
        token = await self._register_and_login(client, "import_invalid@test.com", test_password)
        resp = await client.post(
            "/api/v1/imports/transactions",
            files={"file": ("file.txt", io.BytesIO(b"test"), "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    async def test_list_import_jobs(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "import_list@test.com", test_password)
        resp = await client.get(
            "/api/v1/imports/jobs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "jobs" in resp.json()
