from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.permission import PermissionModel


class PermissionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_name(self, name: str) -> PermissionModel | None:
        result = await self._db.execute(
            select(PermissionModel).where(PermissionModel.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, permission_id: UUID) -> PermissionModel | None:
        result = await self._db.execute(
            select(PermissionModel).where(PermissionModel.id == permission_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[PermissionModel]:
        result = await self._db.execute(
            select(PermissionModel).order_by(PermissionModel.resource, PermissionModel.action)
        )
        return list(result.scalars().all())

    async def list_by_resource(self, resource: str) -> list[PermissionModel]:
        result = await self._db.execute(
            select(PermissionModel)
            .where(PermissionModel.resource == resource)
            .order_by(PermissionModel.action)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> PermissionModel:
        perm = PermissionModel(**kwargs)
        self._db.add(perm)
        await self._db.flush()
        return perm

    async def delete(self, permission_id: UUID) -> bool:
        perm = await self.get_by_id(permission_id)
        if not perm:
            return False
        await self._db.delete(perm)
        await self._db.flush()
        return True
