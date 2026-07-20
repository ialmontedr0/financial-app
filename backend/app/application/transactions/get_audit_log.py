"""Use case: Get audit log for a transaction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class GetAuditLogUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> dict:
        from app.middleware.error_handler import NotFoundError

        tx = await self._repo.get_by_id(transaction_id, user_id)
        if tx is None:
            raise NotFoundError("Transaction")

        logs = await self._repo.get_audit_log(transaction_id)
        return {"transaction_id": str(transaction_id), "audit_logs": [
            {"id": str(log.id), "action": log.action, "changes": log.changes,
             "ip_address": log.ip_address, "user_agent": log.user_agent,
             "created_at": log.created_at.isoformat() if log.created_at else None}
            for log in logs], "total": len(logs)}
