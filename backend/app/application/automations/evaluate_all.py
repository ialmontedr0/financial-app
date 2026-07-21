"""Use case: Evaluate all active automation rules."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class EvaluateAllRulesUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: uuid.UUID, dry_run: bool = False) -> dict:
        from app.automation.engine import AutomationEngine

        engine = AutomationEngine(self._session)
        return await engine.evaluate_all(user_id, dry_run=dry_run)
