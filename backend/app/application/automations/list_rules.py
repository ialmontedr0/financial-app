"""Use case: List automation rules."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ListAutomationRulesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: uuid.UUID,
        is_active: bool | None = None,
        trigger_type: str | None = None,
    ) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rules = await repo.list_rules(
            user_id, is_active=is_active, trigger_type=trigger_type
        )

        return {
            "rules": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "description": r.description,
                    "trigger_type": r.trigger_type,
                    "action_type": r.action_type,
                    "trigger_conditions": r.trigger_conditions,
                    "action_params": r.action_params,
                    "is_active": r.is_active,
                    "execution_count": r.execution_count,
                    "last_executed_at": (
                        r.last_executed_at.isoformat() if r.last_executed_at else None
                    ),
                    "last_execution_status": r.last_execution_status,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rules
            ],
            "total": len(rules),
        }
