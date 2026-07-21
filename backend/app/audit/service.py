from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = AuditRepository(db)

    @property
    def repo(self) -> AuditRepository:
        return self._repo

    async def log_action(
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
    ) -> None:
        await self._repo.log(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )
