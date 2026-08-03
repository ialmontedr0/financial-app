"""Tax API integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestTaxCategories:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_category(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_cat1@test.com", test_password)
        resp = await client.post(
            "/api/v1/taxes/categories",
            json={"name": "Salud", "tax_year": 2025, "description": "Gastos médicos"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Salud"
        assert data["tax_year"] == 2025

    async def test_create_category_invalid_year(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_cat2@test.com", test_password)
        resp = await client.post(
            "/api/v1/taxes/categories",
            json={"name": "Salud", "tax_year": 1700},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_list_categories(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_cat3@test.com", test_password)
        await client.post(
            "/api/v1/taxes/categories",
            json={"name": "Educación", "tax_year": 2025},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/taxes/categories",
            json={"name": "Vivienda", "tax_year": 2024},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            "/api/v1/taxes/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

        filtered = await client.get(
            "/api/v1/taxes/categories?tax_year=2025",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert filtered.json()["total"] == 1

    async def test_delete_category(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_cat4@test.com", test_password)
        create = await client.post(
            "/api/v1/taxes/categories",
            json={"name": "Temporal", "tax_year": 2025},
            headers={"Authorization": f"Bearer {token}"},
        )
        category_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/taxes/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Tax category deleted successfully"


@pytest.mark.api
class TestTaxDeductions:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_category(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/taxes/categories",
            json={"name": "Salud", "tax_year": 2025},
            headers={"Authorization": f"Bearer {token}"},
        )
        return resp.json()["id"]

    async def test_create_deduction(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_ded1@test.com", test_password)
        category_id = await self._create_category(client, token)
        resp = await client.post(
            "/api/v1/taxes/deductions",
            json={
                "description": "Prima de seguro médico",
                "amount": 1500.50,
                "date": "2025-04-10",
                "tax_year": 2025,
                "category_id": category_id,
                "deductible": 1200.00,
                "receipt_url": "https://example.com/receipt.pdf",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["description"] == "Prima de seguro médico"
        assert data["amount"] == 1500.5
        assert data["tax_year"] == 2025
        assert data["category_id"] == category_id

    async def test_create_deduction_invalid_amount(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_ded2@test.com", test_password)
        resp = await client.post(
            "/api/v1/taxes/deductions",
            json={
                "description": "Invalida",
                "amount": -5,
                "date": "2025-04-10",
                "tax_year": 2025,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_list_and_filter_deductions(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_ded3@test.com", test_password)
        category_id = await self._create_category(client, token)
        for i in range(2):
            await client.post(
                "/api/v1/taxes/deductions",
                json={
                    "description": f"Deducción {i}",
                    "amount": 100 + i,
                    "date": "2025-04-10",
                    "tax_year": 2025,
                    "category_id": category_id,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        resp = await client.get(
            "/api/v1/taxes/deductions?tax_year=2025",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

        resp_filtered = await client.get(
            f"/api/v1/taxes/deductions?category_id={category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_filtered.json()["total"] == 2

    async def test_get_deduction(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_ded4@test.com", test_password)
        create = await client.post(
            "/api/v1/taxes/deductions",
            json={
                "description": "Consulta médica",
                "amount": 800,
                "date": "2025-05-01",
                "tax_year": 2025,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        deduction_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/taxes/deductions/{deduction_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Consulta médica"

    async def test_update_deduction(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_ded5@test.com", test_password)
        create = await client.post(
            "/api/v1/taxes/deductions",
            json={
                "description": "Original",
                "amount": 500,
                "date": "2025-05-01",
                "tax_year": 2025,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        deduction_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/taxes/deductions/{deduction_id}",
            json={"description": "Actualizada", "amount": 750},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Actualizada"
        assert data["amount"] == 750

    async def test_delete_deduction(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_ded6@test.com", test_password)
        create = await client.post(
            "/api/v1/taxes/deductions",
            json={
                "description": "Borrar",
                "amount": 300,
                "date": "2025-05-01",
                "tax_year": 2025,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        deduction_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/taxes/deductions/{deduction_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Tax deduction deleted successfully"

    async def test_deduction_not_found_other_user(self, client: AsyncClient, test_password: str):
        token_a = await self._register_and_login(client, "tax_ded7a@test.com", test_password)
        token_b = await self._register_and_login(client, "tax_ded7b@test.com", test_password)
        create = await client.post(
            "/api/v1/taxes/deductions",
            json={
                "description": "Privada",
                "amount": 400,
                "date": "2025-05-01",
                "tax_year": 2025,
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        deduction_id = create.json()["id"]
        resp = await client.get(
            f"/api/v1/taxes/deductions/{deduction_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404


@pytest.mark.api
class TestTaxSummary:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_summary_by_year(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_sum1@test.com", test_password)
        for desc, amount, deductible in [
            ("Médico", 1000, 800),
            ("Educación", 2000, 1200),
        ]:
            await client.post(
                "/api/v1/taxes/deductions",
                json={
                    "description": desc,
                    "amount": amount,
                    "date": "2025-06-01",
                    "tax_year": 2025,
                    "deductible": deductible,
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        resp = await client.get(
            "/api/v1/taxes/summary/2025",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2025
        assert data["total_deductions"] == 3000
        assert data["total_deductible"] == 2000
        assert data["deduction_count"] == 2

    async def test_summary_empty_year(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "tax_sum2@test.com", test_password)
        resp = await client.get(
            "/api/v1/taxes/summary/2024",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_deductions"] == 0
        assert data["total_deductible"] == 0
        assert data["deduction_count"] == 0
