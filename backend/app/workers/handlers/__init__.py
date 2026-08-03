"""Event bus worker handlers."""

from app.workers.handlers.budget_handler import handle_transaction_event as handle_budget_event
from app.workers.handlers.goal_handler import handle_transaction_event as handle_goal_event
from app.workers.handlers.notification_handler import handle_event as handle_notification_event

__all__ = [
    "handle_budget_event",
    "handle_goal_event",
    "handle_notification_event",
]
