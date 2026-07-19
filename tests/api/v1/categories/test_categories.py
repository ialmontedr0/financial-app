"""Tests for category endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.api
class TestCategoryCRUD:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_list_system_categories(self, client: AsyncClient, test_password: str) -> None:
        """System categories should be visible to all users."""
        email = "catlist@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.get(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 20  # At least 26 system categories
        # Verify system categories are present
        names = [c["name"] for c in data["categories"]]
        assert "Alimentacion" in names
        assert "Sin Categoria" in names

    async def test_create_user_category(self, client: AsyncClient, test_password: str) -> None:
        email = "catcreate@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Mi Categoria Custom",
                "category_type": "expense",
                "icon": "🎯",
                "color": "#FF0000",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mi Categoria Custom"
        assert data["is_system"] is False

    async def test_get_category_detail(self, client: AsyncClient, test_password: str) -> None:
        email = "catdetail@test.com"
        token = await self._register_and_login(client, email, test_password)
        # List categories to get an ID
        list_resp = await client.get(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        cat_id = list_resp.json()["categories"][0]["id"]
        response = await client.get(
            f"/api/v1/categories/{cat_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "subcategories" in response.json()

    async def test_update_user_category(self, client: AsyncClient, test_password: str) -> None:
        email = "catupdate@test.com"
        token = await self._register_and_login(client, email, test_password)
        # Create
        create_resp = await client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Old Name", "category_type": "expense"},
        )
        cat_id = create_resp.json()["id"]
        # Update
        response = await client.patch(
            f"/api/v1/categories/{cat_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "New Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_delete_user_category(self, client: AsyncClient, test_password: str) -> None:
        email = "catdelete@test.com"
        token = await self._register_and_login(client, email, test_password)
        create_resp = await client.post(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "To Delete", "category_type": "expense"},
        )
        cat_id = create_resp.json()["id"]
        response = await client.delete(
            f"/api/v1/categories/{cat_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_cannot_delete_system_category(self, client: AsyncClient, test_password: str) -> None:
        email = "catnodelete@test.com"
        token = await self._register_and_login(client, email, test_password)
        # Get system category ID
        list_resp = await client.get(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        system_cat = next(c for c in list_resp.json()["categories"] if c["is_system"])
        response = await client.delete(
            f"/api/v1/categories/{system_cat['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422  # Validation error


@pytest.mark.api
class TestSubcategories:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_create_subcategory(self, client: AsyncClient, test_password: str) -> None:
        email = "subcreate@test.com"
        token = await self._register_and_login(client, email, test_password)
        # Get a category ID
        list_resp = await client.get(
            "/api/v1/categories",
            headers={"Authorization": f"Bearer {token}"},
        )
        cat_id = list_resp.json()["categories"][0]["id"]
        response = await client.post(
            f"/api/v1/categories/{cat_id}/subcategories",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Mi Subcategoria Custom", "icon": "📌"},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Mi Subcategoria Custom"


@pytest.mark.api
class TestCategorize:
    async def _register_and_login(self, client: AsyncClient, email: str, password: str) -> str:
        await client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login_resp.json()["tokens"]["access_token"]

    async def test_categorize_unknown_returns_fallback(self, client: AsyncClient, test_password: str) -> None:
        email = "categorize@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.post(
            "/api/v1/categories/categorize",
            headers={"Authorization": f"Bearer {token}"},
            json={"description": "XYZRANDOM123 merchant"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "fallback"
        assert data["confidence"] == 0.0

    async def test_category_stats(self, client: AsyncClient, test_password: str) -> None:
        email = "catstats@test.com"
        token = await self._register_and_login(client, email, test_password)
        response = await client.get(
            "/api/v1/categories/stats/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_categories"] >= 26
        assert data["system_categories"] >= 26
