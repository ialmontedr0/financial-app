"""Budget event handler - recalculates budgets when transactions change."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

import structlog

from app.domain.events import EventType
from app.infrastructure.repositories.budget_repository import BudgetRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def handle_transaction_event(session: AsyncSession, event: dict[str, Any]) -> int:
    """Recalculate affected budgets and surface alerts after a transaction event.

    Returns the number of budgets refreshed.
    """
    event_type = event.get("event_type")
    if event_type not in (
        EventType.TRANSACTION_CREATED.value,
        EventType.TRANSACTION_UPDATED.value,
        EventType.TRANSACTION_DELETED.value,
    ):
        return 0

    user_id_raw = event.get("user_id")
    data = event.get("data") or {}
    if not user_id_raw:
        return 0

    try:
        user_id = uuid.UUID(str(user_id_raw))
        effective_date = date.fromisoformat(str(data["effective_date"]))
    except (KeyError, ValueError, TypeError):
        logger.warning("budget_event_skipped", reason="invalid_event_data", event_type=event_type)
        return 0

    category_id = uuid.UUID(str(data["category_id"])) if data.get("category_id") else None
    account_id = uuid.UUID(str(data["account_id"])) if data.get("account_id") else None

    repo = BudgetRepository(session)
    budgets = await repo.get_active_budgets_for_period(user_id, effective_date, effective_date)

    from app.application.budgets.refresh_budget import RefreshBudgetUseCase

    refreshed = 0
    for budget in budgets:
        if budget.budget_type == "category" and (
            not budget.category_id or budget.category_id != category_id
        ):
            continue
        if budget.budget_type == "account" and (
            not budget.account_id or budget.account_id != account_id
        ):
            continue
        await RefreshBudgetUseCase(session).execute(user_id, budget.id)
        refreshed += 1

    if refreshed:
        logger.info(
            "budgets_refreshed_from_event",
            user_id=str(user_id),
            event_type=event_type,
            count=refreshed,
        )
    return refreshed
