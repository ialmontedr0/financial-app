"""Integration tests for event bus worker handlers."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.application.transactions.notifications import emit_transaction_notification
from app.domain.events import EventType
from app.infrastructure.models.notification import NotificationModel
from app.infrastructure.models.transaction import TransactionModel
from app.infrastructure.repositories.account_repository import AccountRepository
from app.infrastructure.repositories.budget_repository import BudgetRepository
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher
from app.workers.handlers import (
    handle_budget_event,
    handle_goal_event,
)


@pytest.mark.integration
class TestBudgetEventHandler:
    async def test_recalculates_spent_and_creates_alert(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-budget@test.com", password_hash=PasswordHasher.hash_password(test_password)
        )
        await db_session.commit()

        today = datetime.now(UTC).date()
        budget = await BudgetRepository(db_session).create_budget(
            user.id,
            name="Event Budget",
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

        event = {
            "event_type": EventType.TRANSACTION_CREATED.value,
            "user_id": str(user.id),
            "data": {
                "account_id": None,
                "category_id": None,
                "amount": "150",
                "transaction_type": "expense",
                "effective_date": today.isoformat(),
            },
        }

        refreshed = await handle_budget_event(db_session, event)
        await db_session.commit()

        assert refreshed == 1
        reloaded = await BudgetRepository(db_session).get_budget_by_id(budget.id, user.id)
        assert reloaded is not None
        assert float(reloaded.spent) == 150.0

        alerts = await BudgetRepository(db_session).list_alerts(
            user.id, budget_id=budget.id, alert_type="exceeded"
        )
        assert len(alerts) >= 1

        notif_count = await db_session.execute(
            select(func.count(NotificationModel.id)).where(NotificationModel.user_id == user.id)
        )
        assert notif_count.scalar_one() >= 1

    async def test_skips_unrelated_category_budget(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-budget-other@test.com",
            password_hash=PasswordHasher.hash_password(test_password),
        )
        await db_session.commit()

        today = datetime.now(UTC).date()
        await BudgetRepository(db_session).create_budget(
            user.id,
            name="Category Budget",
            amount=Decimal("100"),
            budget_type="category",
            period="monthly",
            start_date=today,
            end_date=today,
            category_id=None,
        )
        await db_session.commit()

        event = {
            "event_type": EventType.TRANSACTION_CREATED.value,
            "user_id": str(user.id),
            "data": {
                "account_id": None,
                "category_id": None,
                "amount": "150",
                "transaction_type": "expense",
                "effective_date": today.isoformat(),
            },
        }

        refreshed = await handle_budget_event(db_session, event)
        assert refreshed == 0


@pytest.mark.integration
class TestGoalEventHandler:
    async def test_updates_progress_and_emits_milestones(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-goal@test.com", password_hash=PasswordHasher.hash_password(test_password)
        )
        await db_session.commit()

        today = datetime.now(UTC).date()
        goal = await GoalRepository(db_session).create_goal(
            user.id,
            name="Vacaciones",
            goal_type="savings",
            target_amount=Decimal("1000"),
            start_date=today - timedelta(days=30),
            target_date=today + timedelta(days=300),
        )
        await db_session.commit()

        tx = TransactionModel(
            user_id=user.id,
            transaction_type="income",
            status="completed",
            amount=Decimal("500"),
            currency_code="DOP",
            description="salario",
            effective_date=today,
        )
        db_session.add(tx)
        await db_session.commit()

        event = {
            "event_type": EventType.TRANSACTION_CREATED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "income", "amount": "500"},
        }

        evaluated = await handle_goal_event(db_session, event)
        await db_session.commit()

        assert evaluated == 1
        reloaded = await GoalRepository(db_session).get_goal_by_id(goal.id, user.id)
        assert reloaded is not None
        assert float(reloaded.current_amount) == 500.0
        assert reloaded.milestone_reached_pct >= 50

        milestones = await GoalRepository(db_session).list_milestones(goal.id, user.id)
        assert len(milestones) == 2  # crossed 25% and 50%

    async def test_expense_event_reduces_progress(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-goal-expense@test.com",
            password_hash=PasswordHasher.hash_password(test_password),
        )
        await db_session.commit()

        today = datetime.now(UTC).date()
        goal = await GoalRepository(db_session).create_goal(
            user.id,
            name="Ahorro",
            goal_type="savings",
            target_amount=Decimal("1000"),
            start_date=today - timedelta(days=30),
            target_date=today + timedelta(days=300),
        )
        await db_session.commit()

        income_tx = TransactionModel(
            user_id=user.id,
            transaction_type="income",
            status="completed",
            amount=Decimal("500"),
            currency_code="DOP",
            description="salario",
            effective_date=today,
        )
        db_session.add(income_tx)
        await db_session.commit()

        income_event = {
            "event_type": EventType.TRANSACTION_CREATED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "income", "amount": "500"},
        }
        evaluated = await handle_goal_event(db_session, income_event)
        await db_session.commit()
        assert evaluated == 1
        reloaded = await GoalRepository(db_session).get_goal_by_id(goal.id, user.id)
        assert reloaded is not None
        assert float(reloaded.current_amount) == 500.0

        expense_tx = TransactionModel(
            user_id=user.id,
            transaction_type="expense",
            status="completed",
            amount=Decimal("200"),
            currency_code="DOP",
            description="compra",
            effective_date=today,
        )
        db_session.add(expense_tx)
        await db_session.commit()

        expense_event = {
            "event_type": EventType.TRANSACTION_CREATED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "expense", "amount": "200"},
        }
        evaluated = await handle_goal_event(db_session, expense_event)
        await db_session.commit()
        assert evaluated == 1
        reloaded = await GoalRepository(db_session).get_goal_by_id(goal.id, user.id)
        assert reloaded is not None
        assert float(reloaded.current_amount) == 300.0

    async def test_updated_event_recalculates_progress(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-goal-updated@test.com",
            password_hash=PasswordHasher.hash_password(test_password),
        )
        await db_session.commit()

        today = datetime.now(UTC).date()
        goal = await GoalRepository(db_session).create_goal(
            user.id,
            name="Ahorro",
            goal_type="savings",
            target_amount=Decimal("1000"),
            start_date=today - timedelta(days=30),
            target_date=today + timedelta(days=300),
        )
        await db_session.commit()

        tx = TransactionModel(
            user_id=user.id,
            transaction_type="income",
            status="completed",
            amount=Decimal("500"),
            currency_code="DOP",
            description="salario",
            effective_date=today,
        )
        db_session.add(tx)
        await db_session.commit()

        created = {
            "event_type": EventType.TRANSACTION_CREATED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "income", "amount": "500"},
        }
        assert await handle_goal_event(db_session, created) == 1
        await db_session.commit()

        tx.amount = Decimal("700")
        await db_session.commit()

        updated = {
            "event_type": EventType.TRANSACTION_UPDATED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "income", "amount": "700"},
        }
        evaluated = await handle_goal_event(db_session, updated)
        await db_session.commit()

        assert evaluated == 1
        reloaded = await GoalRepository(db_session).get_goal_by_id(goal.id, user.id)
        assert reloaded is not None
        assert float(reloaded.current_amount) == 700.0

    async def test_deleted_event_recalculates_progress(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-goal-deleted@test.com",
            password_hash=PasswordHasher.hash_password(test_password),
        )
        await db_session.commit()

        today = datetime.now(UTC).date()
        goal = await GoalRepository(db_session).create_goal(
            user.id,
            name="Ahorro",
            goal_type="savings",
            target_amount=Decimal("1000"),
            start_date=today - timedelta(days=30),
            target_date=today + timedelta(days=300),
        )
        await db_session.commit()

        tx = TransactionModel(
            user_id=user.id,
            transaction_type="income",
            status="completed",
            amount=Decimal("500"),
            currency_code="DOP",
            description="salario",
            effective_date=today,
        )
        db_session.add(tx)
        await db_session.commit()

        created = {
            "event_type": EventType.TRANSACTION_CREATED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "income", "amount": "500"},
        }
        assert await handle_goal_event(db_session, created) == 1
        await db_session.commit()

        tx.deleted_at = datetime.now(UTC)
        await db_session.commit()

        deleted = {
            "event_type": EventType.TRANSACTION_DELETED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "income", "amount": "500"},
        }
        evaluated = await handle_goal_event(db_session, deleted)
        await db_session.commit()

        assert evaluated == 1
        reloaded = await GoalRepository(db_session).get_goal_by_id(goal.id, user.id)
        assert reloaded is not None
        assert float(reloaded.current_amount) == 0.0

    async def test_skips_non_goal_events(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-goal-skip@test.com",
            password_hash=PasswordHasher.hash_password(test_password),
        )
        await db_session.commit()

        event = {
            "event_type": EventType.RECURRING_TRANSACTION_PROCESSED.value,
            "user_id": str(user.id),
            "data": {"transaction_type": "transfer", "amount": "500"},
        }

        evaluated = await handle_goal_event(db_session, event)
        assert evaluated == 0


@pytest.mark.integration
class TestTransactionNotificationHelper:
    async def test_creates_inapp_notification(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-notif@test.com", password_hash=PasswordHasher.hash_password(test_password)
        )
        account = await AccountRepository(db_session).create(
            user.id, name="Banco", account_type="bank"
        )
        await db_session.commit()

        transaction_id = uuid.uuid4()
        emitted = await emit_transaction_notification(
            db_session,
            user.id,
            transaction_id=transaction_id,
            account_id=account.id,
            amount="1250.50",
            currency_code="DOP",
            action="created",
        )
        await db_session.commit()

        assert emitted is True
        result = await db_session.execute(
            select(NotificationModel).where(NotificationModel.user_id == user.id)
        )
        notif = result.scalar_one()
        assert notif.type == "transaction_alert"
        assert "1250.50" in notif.body
        assert "Banco" in notif.body
        assert notif.channel == "push"
        assert notif.is_sent is True
        assert notif.data["link"] == f"/transactions/{transaction_id}"

    async def test_delete_has_no_link(self, db_session, test_password):
        user_repo = UserRepository(db_session)
        user = await user_repo.create(
            email="event-notif-delete@test.com",
            password_hash=PasswordHasher.hash_password(test_password),
        )
        await db_session.commit()

        transaction_id = uuid.uuid4()
        await emit_transaction_notification(
            db_session,
            user.id,
            transaction_id=transaction_id,
            account_id=None,
            amount="500",
            currency_code="DOP",
            action="deleted",
        )
        await db_session.commit()

        result = await db_session.execute(
            select(NotificationModel).where(NotificationModel.user_id == user.id)
        )
        notif = result.scalar_one()
        assert notif.type == "transaction_alert"
        assert "eliminada" in notif.body
        assert "tu cuenta" in notif.body
        assert notif.data.get("link") is None
