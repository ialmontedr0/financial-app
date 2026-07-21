"""Use case: Execute an automation rule."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ExecuteAutomationRuleUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self, user_id: uuid.UUID, rule_id: uuid.UUID, dry_run: bool = False
    ) -> dict:
        from app.automation.engine import AutomationEngine

        engine = AutomationEngine(self._session)
        return await engine.execute_rule(rule_id, user_id, dry_run=dry_run)
