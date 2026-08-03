"""Domain event value objects for the FIP event bus."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class EventType(str, enum.Enum):  # noqa: UP042
    """Canonical event types published to the domain event bus."""

    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    TRANSACTION_DELETED = "transaction.deleted"
    BUDGET_EXCEEDED = "budget.exceeded"
    BUDGET_UPDATED = "budget.updated"
    GOAL_PROGRESS = "goal.progress"
    GOAL_REACHED = "goal.reached"
    GOAL_UPDATED = "goal.updated"
    RECURRING_TRANSACTION_PROCESSED = "recurring.processed"
    USER_REGISTERED = "user.registered"
    ACCOUNT_BALANCE_CHANGED = "account.balance_changed"
    NOTIFICATION_CREATED = "notification.created"
    SUBSCRIPTION_EXPIRING = "subscription.expiring"


@dataclass(frozen=True)
class DomainEvent:
    """In-memory representation of a published domain event."""

    event_type: EventType
    aggregate_id: uuid.UUID
    aggregate_type: str
    user_id: uuid.UUID | None = None
    data: dict[str, Any] = field(default_factory=dict)
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
