"""Use case: Update automation rule."""

from __future__ import annotations

import uuid
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UpdateAutomationRuleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self, user_id: uuid.UUID, rule_id: uuid.UUID, **kwargs: Any
    ) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        rule = await repo.update_rule(rule_id, user_id, **kwargs)
        if rule is None:
            return {"error": "Rule not found"}

        return {
            "id": str(rule.id),
            "name": rule.name,
            "message": "Rule updated successfully",
        }
