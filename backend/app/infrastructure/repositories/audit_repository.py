from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.system_audit_log import SystemAuditLogModel


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log(
        self,
        *,
        user_id: UUID | None,
        action: str,
        resource: str,
        resource_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
    ) -> SystemAuditLogModel:
        entry = SystemAuditLogModel(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )
        self._db.add(entry)
        await self._db.flush()
        return entry

    async def list_logs(
        self,
        *,
        user_id: UUID | None = None,
        action: str | None = None,
        resource: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SystemAuditLogModel]:
        query = select(SystemAuditLogModel)
        filters = []
        if user_id:
            filters.append(SystemAuditLogModel.user_id == user_id)
        if action:
            filters.append(SystemAuditLogModel.action == action)
        if resource:
            filters.append(SystemAuditLogModel.resource == resource)
        if status:
            filters.append(SystemAuditLogModel.status == status)
        if start_date:
            filters.append(SystemAuditLogModel.created_at >= start_date)
        if end_date:
            filters.append(SystemAuditLogModel.created_at <= end_date)
        if filters:
            query = query.where(and_(*filters))
        query = query.order_by(SystemAuditLogModel.created_at.desc()).offset(skip).limit(limit)
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, log_id: UUID) -> SystemAuditLogModel | None:
        result = await self._db.execute(
            select(SystemAuditLogModel).where(SystemAuditLogModel.id == log_id)
        )
        return result.scalar_one_or_none()

    async def count_logs(
        self,
        *,
        user_id: UUID | None = None,
        action: str | None = None,
        resource: str | None = None,
    ) -> int:
        query = select(func.count(SystemAuditLogModel.id))
        filters = []
        if user_id:
            filters.append(SystemAuditLogModel.user_id == user_id)
        if action:
            filters.append(SystemAuditLogModel.action == action)
        if resource:
            filters.append(SystemAuditLogModel.resource == resource)
        if filters:
            query = query.where(and_(*filters))
        result = await self._db.execute(query)
        return result.scalar() or 0

    async def stats(self) -> dict[str, Any]:
        total_q = await self._db.execute(select(func.count(SystemAuditLogModel.id)))
        total = total_q.scalar() or 0

        action_q = await self._db.execute(
            select(SystemAuditLogModel.action, func.count(SystemAuditLogModel.id))
            .group_by(SystemAuditLogModel.action)
        )
        by_action: dict[str, int] = dict(action_q.all())

        resource_q = await self._db.execute(
            select(SystemAuditLogModel.resource, func.count(SystemAuditLogModel.id))
            .group_by(SystemAuditLogModel.resource)
        )
        by_resource: dict[str, int] = dict(resource_q.all())

        status_q = await self._db.execute(
            select(SystemAuditLogModel.status, func.count(SystemAuditLogModel.id))
            .group_by(SystemAuditLogModel.status)
        )
        by_status: dict[str, int] = dict(status_q.all())

        return {"total": total, "by_action": by_action, "by_resource": by_resource, "by_status": by_status}
