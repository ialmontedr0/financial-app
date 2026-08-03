"""End-to-end tests for the event bus: publish -> stream -> process -> handlers."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.domain.events import EventType
from app.infrastructure.cache.redis import redis_client
from app.infrastructure.eventbus import EVENT_STREAM, EventPublisher, publish_event
from app.infrastructure.models.domain_event import DomainEventModel
from app.infrastructure.models.transaction import TransactionModel
from app.infrastructure.repositories.budget_repository import BudgetRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher
from app.workers.process_events import process_events


async def _clear_stream() -> None:
    await redis_client.delete(EVENT_STREAM)


@pytest.mark.integration
class TestEventBus:
    async def test_publish_event_returns_event_id(self):
        await _clear_stream()
        try:
            event_id = await publish_event(
                event_type=EventType.USER_REGISTERED,
                aggregate_id=uuid.uuid4(),
                aggregate_type="user",
                data={"email": "x@test.com"},
            )
            assert event_id is not None
            length = await redis_client.xlen(EVENT_STREAM)
            assert length == 1
        finally:
            await _clear_stream()

    async def test_publish_and_process_end_to_end(self, db_session, test_password):
        await _clear_stream()
        try:
            user = await UserRepository(db_session).create(
                email="event-bus@test.com", password_hash=PasswordHasher.hash_password(test_password)
            )
            await db_session.commit()

            today = date.today()  # noqa: DTZ011
            budget = await BudgetRepository(db_session).create_budget(
                user.id,
                name="Bus Budget",
                amount=Decimal("100"),
                budget_type="total",
                period="monthly",
                start_date=today,
                end_date=today,
            )
            await db_session.commit()

            tx = TransactionModel(
                user_id=user.id,
                transaction_type="expense",
                status="completed",
                amount=Decimal("150"),
                currency_code="DOP",
                description="compra",
                effective_date=today,
            )
            db_session.add(tx)
            await db_session.commit()

            publisher = EventPublisher(redis_client)
            await publisher.publish(
                event_type=EventType.TRANSACTION_CREATED,
                aggregate_id=tx.id,
                aggregate_type="transaction",
                user_id=user.id,
                data={
                    "transaction_id": str(tx.id),
                    "account_id": None,
                    "category_id": None,
                    "amount": "150",
                    "transaction_type": "expense",
                    "effective_date": today.isoformat(),
                },
            )
            assert await redis_client.xlen(EVENT_STREAM) == 1

            processed = await process_events({"db": db_session})
            assert processed == 1

            reloaded = await BudgetRepository(db_session).get_budget_by_id(budget.id, user.id)
            assert reloaded is not None
            assert float(reloaded.spent) == 150.0

            audit = await db_session.execute(
                select(func.count(DomainEventModel.id)).where(
                    DomainEventModel.status == "processed",
                    DomainEventModel.aggregate_id == tx.id,
                )
            )
            assert audit.scalar_one() == 1

            assert await redis_client.xlen(EVENT_STREAM) == 0
        finally:
            await _clear_stream()
