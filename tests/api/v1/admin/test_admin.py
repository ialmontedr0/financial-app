"""Phase 19 Admin API tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.user import UserModel


@pytest.mark.api
class TestAdminRoles:
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

    async def _promote_to_admin(
        self, db: AsyncSession, email: str
    ) -> None:
        """Promote a user to admin role directly in the DB."""
        await db.execute(
            update(UserModel).where(UserModel.email == email).values(role="admin")
        )
        await db.commit()

    async def test_list_roles(
        self, client: AsyncClient, test_password: str, db_session: AsyncSession
    ):
        email = "admin_roles@test.com"
        token = await self._register_and_login(client, email, test_password)
        await self._promote_to_admin(db_session, email)
        resp = await client.get(
            "/api/v1/admin/roles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "roles" in data
        assert data["total"] >= 3  # user, moderator, admin seeded

    async def test_create_role(
        self, client: AsyncClient, test_password: str, db_session: AsyncSession
    ):
        email = "admin_create_role@test.com"
        token = await self._register_and_login(client, email, test_password)
        await self._promote_to_admin(db_session, email)
        resp = await client.post(
            "/api/v1/admin/roles",
            json={
                "name": "premium",
                "display_name": "Premium User",
                "description": "Premium tier user",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "premium"

    async def test_list_permissions(
        self, client: AsyncClient, test_password: str, db_session: AsyncSession
    ):
        email = "admin_perms@test.com"
        token = await self._register_and_login(client, email, test_password)
        await self._promote_to_admin(db_session, email)
        resp = await client.get(
            "/api/v1/admin/permissions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 18  # seeded permissions

    async def test_list_users(
        self, client: AsyncClient, test_password: str, db_session: AsyncSession
    ):
        email = "admin_list_users@test.com"
        token = await self._register_and_login(client, email, test_password)
        await self._promote_to_admin(db_session, email)
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert data["total"] >= 1

    async def test_audit_logs(
        self, client: AsyncClient, test_password: str, db_session: AsyncSession
    ):
        email = "admin_audit@test.com"
        token = await self._register_and_login(client, email, test_password)
        await self._promote_to_admin(db_session, email)
        resp = await client.get(
            "/api/v1/admin/audit",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data

    async def test_system_stats(
        self, client: AsyncClient, test_password: str, db_session: AsyncSession
    ):
        email = "admin_stats@test.com"
        token = await self._register_and_login(client, email, test_password)
        await self._promote_to_admin(db_session, email)
        resp = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_roles" in data

    async def test_non_admin_cannot_access(self, client: AsyncClient, test_password: str):
        token = await self._register_and_login(
            client, "regular_user@test.com", test_password
        )
        resp = await client.get(
            "/api/v1/admin/roles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    async def test_update_user_role(
        self, client: AsyncClient, test_password: str, db_session: AsyncSession
    ):
        admin_email = "admin_change_role@test.com"
        token = await self._register_and_login(client, admin_email, test_password)
        await self._promote_to_admin(db_session, admin_email)

        # Register a separate regular user as the target
        target_email = "target_user_role@test.com"
        await self._register_and_login(client, target_email, test_password)

        # Get users to find the target
        users_resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        users = users_resp.json()["users"]
        target_user = next(u for u in users if u["email"] == target_email)

        resp = await client.put(
            f"/api/v1/admin/users/{target_user['id']}/role",
            json={"role": "moderator"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_role"] == "moderator"

    async def test_unauthorized_access(self, client: AsyncClient):
        resp = await client.get("/api/v1/admin/roles")
        assert resp.status_code in (401, 422)
