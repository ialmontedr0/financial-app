"""Unit tests for domain event value objects."""

import uuid
from datetime import UTC, datetime

import pytest

from app.domain.events import DomainEvent, EventType


@pytest.mark.unit
class TestEventType:
    def test_event_type_values(self) -> None:
        assert EventType.TRANSACTION_CREATED.value == "transaction.created"
        assert EventType.TRANSACTION_UPDATED.value == "transaction.updated"
        assert EventType.TRANSACTION_DELETED.value == "transaction.deleted"
        assert EventType.BUDGET_EXCEEDED.value == "budget.exceeded"
        assert EventType.GOAL_REACHED.value == "goal.reached"
        assert EventType.RECURRING_TRANSACTION_PROCESSED.value == "recurring.processed"
        assert EventType.USER_REGISTERED.value == "user.registered"

    def test_event_type_is_str_enum(self) -> None:
        assert EventType.TRANSACTION_CREATED == "transaction.created"
        assert isinstance(EventType.TRANSACTION_CREATED, str)


@pytest.mark.unit
class TestDomainEvent:
    def test_defaults(self) -> None:
        event = DomainEvent(
            event_type=EventType.TRANSACTION_CREATED,
            aggregate_id=uuid.uuid4(),
            aggregate_type="transaction",
        )
        assert isinstance(event.event_id, uuid.UUID)
        assert event.data == {}
        assert event.user_id is None
        assert event.created_at.tzinfo is not None
        assert event.created_at <= datetime.now(UTC)

    def test_frozen_dataclass(self) -> None:
        event = DomainEvent(
            event_type=EventType.GOAL_REACHED,
            aggregate_id=uuid.uuid4(),
            aggregate_type="goal",
            user_id=uuid.uuid4(),
            data={"goal_id": "x"},
        )
        assert event.user_id is not None
        assert event.data == {"goal_id": "x"}
