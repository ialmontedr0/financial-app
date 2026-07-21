from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import and_, select

from app.infrastructure.models.role import RoleModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class RoleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_name(self, name: str) -> RoleModel | None:
        result = await self._db.execute(
            select(RoleModel).where(RoleModel.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, role_id: UUID) -> RoleModel | None:
        result = await self._db.execute(
            select(RoleModel).where(RoleModel.id == role_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, include_inactive: bool = False) -> list[RoleModel]:
        query = select(RoleModel)
        if not include_inactive:
            query = query.where(RoleModel.is_active == True)  # noqa: E712
        query = query.order_by(RoleModel.name)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> RoleModel:
        role = RoleModel(**kwargs)
        self._db.add(role)
        await self._db.flush()
        return role

    async def update(self, role: RoleModel, **kwargs: Any) -> RoleModel:
        for k, v in kwargs.items():
            if hasattr(role, k):
                setattr(role, k, v)
        await self._db.flush()
        return role

    async def delete(self, role_id: UUID) -> bool:
        role = await self.get_by_id(role_id)
        if not role or role.is_system:
            return False
        await self._db.delete(role)
        await self._db.flush()
        return True

    async def assign_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        from app.infrastructure.models.role_permission import RolePermissionModel

        existing = await self._db.execute(
            select(RolePermissionModel).where(
                and_(
                    RolePermissionModel.role_id == role_id,
                    RolePermissionModel.permission_id == permission_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            return False

        rp = RolePermissionModel(role_id=role_id, permission_id=permission_id)
        self._db.add(rp)
        await self._db.flush()
        return True

    async def remove_permission(self, role_id: UUID, permission_id: UUID) -> bool:
        from app.infrastructure.models.role_permission import RolePermissionModel

        result = await self._db.execute(
            select(RolePermissionModel).where(
                and_(
                    RolePermissionModel.role_id == role_id,
                    RolePermissionModel.permission_id == permission_id,
                )
            )
        )
        rp = result.scalar_one_or_none()
        if not rp:
            return False
        await self._db.delete(rp)
        await self._db.flush()
        return True
