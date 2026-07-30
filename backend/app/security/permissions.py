from __future__ import annotations

import time
from typing import TYPE_CHECKING

from app.infrastructure.models.role import RoleModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class PermissionChecker:
    """Verifies user permissions using in-memory cache."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[set[str], float]] = {}

        self._cache_ttl = 300  # 5 minutos

    def _get_cached(self, key: str) -> set[str] | None:
        entry = self._cache.get(key)
        if entry and time.monotonic() - entry[1] < self._cache_ttl:
            return entry[0]
        if key in self._cache:
            del self._cache[key]
        return None

    def _set_cache(self, key: str, permissions: set[str]):
        self._cache[key] = (permissions, time.monotonic())

    def _cache_key(self, user_id: UUID) -> str:
        return str(user_id)

    async def get_user_permissions(self, user_id: UUID, db: AsyncSession) -> set[str]:
        key = self._cache_key(user_id)
        if key in self._cache:
            return self._cache[key]

        from sqlalchemy import select

        from app.infrastructure.models.role import RoleModel
        from app.infrastructure.models.user import UserModel

        result = await db.execute(select(UserModel).where(UserModel.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return set()

        role_result = await db.execute(select(RoleModel).where(RoleModel.name == user.role))
        role = role_result.scalar_one_or_none()
        if not role:
            return set()

        permissions: set[str] = set()
        await self._collect_permissions(role, permissions, db)
        self._cache[key] = permissions
        return permissions

    async def _collect_permissions(
        self,
        role: RoleModel,
        permissions: set[str],
        db: AsyncSession,
    ) -> None:
        for perm in role.permissions:
            permissions.add(perm.name)

        if role.parent_role_id:
            from sqlalchemy import select

            from app.infrastructure.models.role import RoleModel as RM

            parent_result = await db.execute(select(RM).where(RM.id == role.parent_role_id))
            parent = parent_result.scalar_one_or_none()
            if parent:
                await self._collect_permissions(parent, permissions, db)

    def invalidate(self, user_id: UUID) -> None:
        self._cache.pop(self._cache_key(user_id), None)

    def invalidate_all(self) -> None:
        self._cache.clear()


permission_checker = PermissionChecker()
