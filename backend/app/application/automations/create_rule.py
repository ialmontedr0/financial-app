"""Use case: Create automation rule."""

from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class CreateAutomationRuleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, **kwargs: Any) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        valid_triggers = {
            "income_received",
            "balance_threshold",
            "date_scheduled",
            "bill_due_soon",
            "budget_exceeded",
            "goal_completed",
        }
        trigger_type = kwargs.get("trigger_type", "")
        if trigger_type not in valid_triggers:
            return {
                "error": f"Invalid trigger_type: {trigger_type}. Valid: {valid_triggers}"
            }

        valid_actions = {
            "transfer",
            "pay_credit_card",
            "create_transaction",
            "notify",
            "adjust_budget",
        }
        action_type = kwargs.get("action_type", "")
        if action_type not in valid_actions:
            return {
                "error": f"Invalid action_type: {action_type}. Valid: {valid_actions}"
            }

        repo = AutomationRepository(self._session)
        rule = await repo.create_rule(
            user_id=user_id,
            name=kwargs["name"],
            description=kwargs.get("description"),
            trigger_type=trigger_type,
            action_type=action_type,
            trigger_conditions=kwargs.get("trigger_conditions"),
            action_params=kwargs.get("action_params"),
            max_executions_per_month=kwargs.get("max_executions_per_month"),
            min_balance_required=kwargs.get("min_balance_required"),
        )

        return {
            "id": str(rule.id),
            "name": rule.name,
            "trigger_type": rule.trigger_type,
            "action_type": rule.action_type,
            "is_active": rule.is_active,
            "message": "Automation rule created successfully",
        }
