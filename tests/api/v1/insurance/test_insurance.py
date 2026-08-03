"""Insurance API integration tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient


def _iso(days_from_today: int = 0) -> str:
    return (datetime.now(UTC).date() + timedelta(days=days_from_today)).isoformat()


@pytest.mark.api
class TestInsuranceCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_insurance(
        self, client: AsyncClient, token: str, name: str = "Seguro Auto"
    ) -> str:
        resp = await client.post(
            "/api/v1/insurance",
            json={
                "name": name,
                "type": "auto",
                "provider": "Mapfre",
                "policy_number": "POL-001",
                "status": "active",
                "start_date": _iso(-30),
                "premium_amount": 1200,
                "premium_frequency": "annual",
                "coverage_amount": 50000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        return resp.json()["id"]

    async def test_create_insurance(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_cr1@test.com", test_password)
        resp = await client.post(
            "/api/v1/insurance",
            json={
                "name": "Seguro Vida",
                "type": "life",
                "provider": "Seguros Universal",
                "status": "active",
                "start_date": _iso(-10),
                "end_date": _iso(350),
                "premium_amount": 2500,
                "premium_frequency": "monthly",
                "coverage_amount": 1000000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Seguro Vida"
        assert data["type"] == "life"
        assert data["status"] == "active"
        assert data["premium_amount"] == 2500

    async def test_create_insurance_invalid_type(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_cr2@test.com", test_password)
        resp = await client.post(
            "/api/v1/insurance",
            json={
                "name": "Invalido",
                "type": "pet",
                "start_date": _iso(),
                "premium_amount": 100,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_list_insurances(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_ls1@test.com", test_password)
        await self._create_insurance(client, token)
        resp = await client.get(
            "/api/v1/insurance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["insurances"][0]["provider"] == "Mapfre"

    async def test_get_insurance(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_get1@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        resp = await client.get(
            f"/api/v1/insurance/{insurance_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["policy_number"] == "POL-001"

    async def test_update_insurance(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_up1@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        resp = await client.patch(
            f"/api/v1/insurance/{insurance_id}",
            json={"provider": "La Colonial", "premium_amount": 1500},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "La Colonial"
        assert data["premium_amount"] == 1500

    async def test_update_status(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_st1@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        resp = await client.patch(
            f"/api/v1/insurance/{insurance_id}/status",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    async def test_delete_insurance(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_del1@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        resp = await client.delete(
            f"/api/v1/insurance/{insurance_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Insurance deleted successfully"

        missing = await client.get(
            f"/api/v1/insurance/{insurance_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert missing.status_code == 404


@pytest.mark.api
class TestInsurancePolicies:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_insurance(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/insurance",
            json={
                "name": "Seguro Salud",
                "type": "health",
                "start_date": _iso(-30),
                "premium_amount": 3000,
                "premium_frequency": "monthly",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        return resp.json()["id"]

    async def test_create_policy(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_pol1@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        resp = await client.post(
            f"/api/v1/insurance/{insurance_id}/policies",
            json={
                "name": "Cobertura Hospitalaria",
                "description": "Internamiento",
                "coverage_details": "Habitación privada",
                "deductible": 1000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Cobertura Hospitalaria"
        assert data["deductible"] == 1000

    async def test_list_policies(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_pol2@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        await client.post(
            f"/api/v1/insurance/{insurance_id}/policies",
            json={"name": "Póliza A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            f"/api/v1/insurance/{insurance_id}/policies",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    async def test_delete_policy(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_pol3@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        create = await client.post(
            f"/api/v1/insurance/{insurance_id}/policies",
            json={"name": "Póliza B"},
            headers={"Authorization": f"Bearer {token}"},
        )
        policy_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/insurance/{insurance_id}/policies/{policy_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Policy deleted successfully"


@pytest.mark.api
class TestInsurancePremiums:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def _create_insurance(self, client: AsyncClient, token: str) -> str:
        resp = await client.post(
            "/api/v1/insurance",
            json={
                "name": "Seguro Hogar",
                "type": "home",
                "start_date": _iso(-30),
                "premium_amount": 800,
                "premium_frequency": "monthly",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        return resp.json()["id"]

    async def test_create_premium(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_prm1@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        resp = await client.post(
            f"/api/v1/insurance/{insurance_id}/premiums",
            json={
                "amount": 800,
                "due_date": _iso(10),
                "payment_method": "auto_debit",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["amount"] == 800
        assert data["status"] in ("pending", "overdue")

    async def test_list_premiums(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_prm2@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        await client.post(
            f"/api/v1/insurance/{insurance_id}/premiums",
            json={"amount": 800, "due_date": _iso(5)},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = await client.get(
            f"/api/v1/insurance/{insurance_id}/premiums",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["total_pending_amount"] == 800

    async def test_mark_premium_paid(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_prm3@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        create = await client.post(
            f"/api/v1/insurance/{insurance_id}/premiums",
            json={"amount": 800, "due_date": _iso(-5)},
            headers={"Authorization": f"Bearer {token}"},
        )
        premium_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/insurance/{insurance_id}/premiums/{premium_id}",
            json={"payment_method": "cash"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "paid"
        assert data["paid_date"] == _iso()

    async def test_delete_premium(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_prm4@test.com", test_password)
        insurance_id = await self._create_insurance(client, token)
        create = await client.post(
            f"/api/v1/insurance/{insurance_id}/premiums",
            json={"amount": 800, "due_date": _iso(5)},
            headers={"Authorization": f"Bearer {token}"},
        )
        premium_id = create.json()["id"]
        resp = await client.delete(
            f"/api/v1/insurance/{insurance_id}/premiums/{premium_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Premium deleted successfully"


@pytest.mark.api
class TestInsuranceDashboard:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_dashboard(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_dash1@test.com", test_password)
        annual = await client.post(
            "/api/v1/insurance",
            json={
                "name": "Seguro Anual",
                "type": "life",
                "start_date": _iso(-30),
                "premium_amount": 1200,
                "premium_frequency": "annual",
                "coverage_amount": 500000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        monthly = await client.post(
            "/api/v1/insurance",
            json={
                "name": "Seguro Mensual",
                "type": "health",
                "start_date": _iso(-30),
                "premium_amount": 50,
                "premium_frequency": "monthly",
                "coverage_amount": 100000,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            f"/api/v1/insurance/{annual.json()['id']}/premiums",
            json={"amount": 1200, "due_date": _iso(-5)},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            f"/api/v1/insurance/{monthly.json()['id']}/premiums",
            json={"amount": 50, "due_date": _iso(30)},
            headers={"Authorization": f"Bearer {token}"},
        )

        resp = await client.get(
            "/api/v1/insurance/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_policies"] == 2
        assert data["total_monthly_premiums"] == 150
        assert data["due_premiums"] == 1
        assert data["total_coverage"] == 600000

    async def test_dashboard_empty(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(client, "ins_dash2@test.com", test_password)
        resp = await client.get(
            "/api/v1/insurance/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_policies"] == 0
        assert data["total_monthly_premiums"] == 0
        assert data["due_premiums"] == 0
