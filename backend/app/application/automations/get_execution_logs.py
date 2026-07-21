"""Use case: Get automation execution logs."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class GetExecutionLogsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        rule_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        logs = await repo.list_execution_logs(user_id, rule_id=rule_id, limit=limit)

        return {
            "logs": [
                {
                    "id": str(log.id),
                    "rule_id": str(log.rule_id),
                    "status": log.status,
                    "trigger_snapshot": log.trigger_snapshot,
                    "action_result": log.action_result,
                    "error_message": log.error_message,
                    "amount_involved": (
                        float(log.amount_involved) if log.amount_involved else None
                    ),
                    "source_account_id": (
                        str(log.source_account_id)
                        if log.source_account_id
                        else None
                    ),
                    "target_account_id": (
                        str(log.target_account_id)
                        if log.target_account_id
                        else None
                    ),
                    "is_dry_run": log.is_dry_run,
                    "executed_at": (
                        log.executed_at.isoformat() if log.executed_at else None
                    ),
                }
                for log in logs
            ],
            "total": len(logs),
        }
