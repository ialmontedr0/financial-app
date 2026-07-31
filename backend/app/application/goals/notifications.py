"""Goal milestone notification helpers.

Emits in-app and channel notifications whenever a goal crosses a
milestone threshold (25/50/75/90/100%). Delivery respects the user's
notification preferences (per channel and per notification type).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

MILESTONE_THRESHOLDS = (25, 50, 75, 90, 100)


def crossed_milestones(previous_pct: int, current_pct: float) -> list[int]:
    """Return milestone thresholds crossed between two progress values."""
    return [ms for ms in MILESTONE_THRESHOLDS if ms > previous_pct and current_pct >= ms]


async def emit_goal_milestone_notifications(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    goal_id: uuid.UUID,
    goal_name: str,
    current_amount: float,
    target_amount: float,
    previous_pct: int,
    current_pct: float,
) -> list[str]:
    """Create milestone records and notifications for crossed thresholds.

    Returns the list of emitted event types (e.g. ``["milestone_25"]``).
    """
    milestones = crossed_milestones(previous_pct, current_pct)
    if not milestones:
        return []

    from app.infrastructure.repositories.goal_repository import GoalRepository
    from app.notifications.service import NotificationService

    repo = GoalRepository(session)
    service = NotificationService(session)
    emitted: list[str] = []

    for ms in milestones:
        event_type = "goal_completed" if ms == 100 else f"milestone_{ms}"
        await repo.create_milestone(
            user_id,
            goal_id=goal_id,
            event_type=event_type,
            amount_at_event=current_amount,
            target_amount=target_amount,
            pct_complete=current_pct,
            notes=f"Milestone {ms}% reached",
        )

        if ms == 100:
            notif_type = "goal_completed"
            title = f"Meta completada: {goal_name}"
            body = f"Felicidades, alcanzaste el 100% de tu meta '{goal_name}'."
        else:
            notif_type = "goal_milestone"
            title = f"Hito alcanzado: {ms}% en {goal_name}"
            body = f"Tu meta '{goal_name}' está al {ms}% del objetivo."

        await service.send(
            user_id=user_id,
            type=notif_type,
            title=title,
            body=body,
            data={
                "goal_id": str(goal_id),
                "goal_name": goal_name,
                "pct_complete": current_pct,
                "milestone": ms,
            },
        )
        emitted.append(event_type)

        logger.info(
            "goal_milestone_notification",
            user_id=str(user_id),
            goal_id=str(goal_id),
            milestone=ms,
            notif_type=notif_type,
        )

    return emitted
