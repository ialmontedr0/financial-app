"""Use case: Get automation rule."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class GetAutomationRuleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rule = await repo.get_rule(rule_id, user_id)
        if rule is None:
            return {"error": "Rule not found"}

        return {
            "id": str(rule.id),
            "name": rule.name,
            "description": rule.description,
            "trigger_type": rule.trigger_type,
            "trigger_conditions": rule.trigger_conditions,
            "action_type": rule.action_type,
            "action_params": rule.action_params,
            "is_active": rule.is_active,
            "max_executions_per_month": rule.max_executions_per_month,
            "min_balance_required": (
                float(rule.min_balance_required)
                if rule.min_balance_required
                else None
            ),
            "execution_count": rule.execution_count,
            "last_executed_at": (
                rule.last_executed_at.isoformat() if rule.last_executed_at else None
            ),
            "last_execution_status": rule.last_execution_status,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
        }
