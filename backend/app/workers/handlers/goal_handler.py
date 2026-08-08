"""Goal event handler - recalculates goal progress when income/expense transactions land."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import structlog

from app.domain.events import EventType
from app.infrastructure.repositories.goal_repository import GoalRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

_TRANSACTION_EVENTS = {
    EventType.TRANSACTION_CREATED.value,
    EventType.TRANSACTION_UPDATED.value,
    EventType.TRANSACTION_DELETED.value,
}


async def handle_transaction_event(session: AsyncSession, event: dict[str, Any]) -> int:
    """Recalculate active goals and emit milestone notifications.

    Se recalcula tanto con ingresos como con gastos (creados, actualizados o
    eliminados), ya que ambos modifican el avance hacia la meta.

    Returns the number of goals evaluated.
    """
    if event.get("event_type") not in _TRANSACTION_EVENTS:
        return 0

    data = event.get("data") or {}
    if data.get("transaction_type") not in ("income", "expense"):
        return 0

    user_id_raw = event.get("user_id")
    if not user_id_raw:
        return 0

    try:
        user_id = uuid.UUID(str(user_id_raw))
    except (ValueError, TypeError):
        logger.warning("goal_event_skipped", reason="invalid_user_id")
        return 0

    repo = GoalRepository(session)
    goals = await repo.list_goals(user_id, status="active")

    from app.application.goals.notifications import emit_goal_milestone_notifications

    evaluated = 0
    for goal in goals:
        previous_pct = goal.milestone_reached_pct
        recalculated = await repo.recalculate_progress(goal.id, user_id)
        if recalculated is None:
            continue

        target = float(goal.target_amount)
        current = float(goal.current_amount)
        current_pct = round(min(current / target * 100, 100), 2) if target > 0 else 0.0

        if current_pct > previous_pct:
            await emit_goal_milestone_notifications(
                session,
                user_id,
                goal_id=goal.id,
                goal_name=goal.name,
                current_amount=current,
                target_amount=target,
                previous_pct=previous_pct,
                current_pct=current_pct,
            )
        evaluated += 1

    if evaluated:
        logger.info(
            "goals_evaluated_from_event",
            user_id=str(user_id),
            count=evaluated,
        )
    return evaluated
