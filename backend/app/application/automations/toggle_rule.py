"""Use case: Toggle automation rule active/inactive."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ToggleAutomationRuleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rule = await repo.toggle_rule(rule_id, user_id)
        if rule is None:
            return {"error": "Rule not found"}

        return {
            "id": str(rule.id),
            "name": rule.name,
            "is_active": rule.is_active,
            "message": f"Rule {'activated' if rule.is_active else 'deactivated'}",
        }
