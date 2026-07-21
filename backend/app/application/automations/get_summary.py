"""Use case: Get automation summary."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class GetAutomationSummaryUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rules = await repo.list_rules(user_id)
        logs = await repo.list_execution_logs(user_id, limit=10)

        active_rules = [r for r in rules if r.is_active]
        total_executions = sum(r.execution_count for r in rules)
        success_count = sum(1 for l in logs if l.status == "success")
        failed_count = sum(1 for l in logs if l.status == "failed")

        by_trigger: dict[str, int] = {}
        for r in rules:
            by_trigger[r.trigger_type] = by_trigger.get(r.trigger_type, 0) + 1

        return {
            "total_rules": len(rules),
            "active_rules": len(active_rules),
            "total_executions": total_executions,
            "recent_logs": {
                "success": success_count,
                "failed": failed_count,
            },
            "rules_by_trigger": by_trigger,
            "recent_executions": [
                {
                    "id": str(log.id),
                    "rule_id": str(log.rule_id),
                    "status": log.status,
                    "amount_involved": (
                        float(log.amount_involved) if log.amount_involved else None
                    ),
                    "executed_at": (
                        log.executed_at.isoformat() if log.executed_at else None
                    ),
                }
                for log in logs
            ],
        }
