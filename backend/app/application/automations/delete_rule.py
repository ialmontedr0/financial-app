"""Use case: Delete automation rule."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DeleteAutomationRuleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, rule_id: uuid.UUID) -> dict:
        from app.infrastructure.repositories.automation_repository import (
            AutomationRepository,
        )

        repo = AutomationRepository(self._session)
        deleted = await repo.delete_rule(rule_id, user_id)
        if not deleted:
            return {"error": "Rule not found"}

        return {"message": "Rule deleted successfully"}
