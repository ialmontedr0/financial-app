"""Integrity tests for FK ON DELETE behaviour.

These tests hard-delete parents through the ORM and assert the database-level
ON DELETE CASCADE / SET NULL rules keep referential integrity intact.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.infrastructure.models.budget_alert import BudgetAlertModel
from app.infrastructure.models.card_alert import CardAlertModel
from app.infrastructure.models.card_spending_limit import CardSpendingLimitModel
from app.infrastructure.models.category import CategoryModel
from app.infrastructure.models.credit_card import CreditCardModel
from app.infrastructure.models.debit_card import DebitCardModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.financial_goal import FinancialGoalModel
from app.infrastructure.models.goal_milestone import GoalMilestoneModel
from app.infrastructure.models.income import IncomeModel
from app.infrastructure.models.income_schedule import IncomeScheduleModel
from app.infrastructure.models.notification import NotificationModel
from app.infrastructure.models.subcategory import SubcategoryModel
from app.infrastructure.models.telegram_link_code import TelegramLinkCodeModel
from app.infrastructure.models.transaction import TransactionModel
from app.infrastructure.models.transaction_attachment import TransactionAttachmentModel
from app.infrastructure.models.transaction_audit_log import TransactionAuditLogModel
from app.infrastructure.models.transaction_recurring import TransactionRecurringModel
from app.infrastructure.models.transaction_tag import TransactionTagModel
from app.infrastructure.models.user import UserModel
from app.infrastructure.models.wallet import WalletModel
from app.infrastructure.models.wallet_account import WalletAccountModel


def _unique_email() -> str:
    return f"cascade-{uuid.uuid4().hex[:12]}@example.com"


async def _count(db_session, model, **filters) -> int:
    stmt = select(func.count()).select_from(model)
    for column, value in filters.items():
        stmt = stmt.where(getattr(model, column) == value)
    result = await db_session.execute(stmt)
    return int(result.scalar_one())


async def _create_user(db_session) -> UserModel:
    user = UserModel(email=_unique_email(), password_hash=f"hashed-{uuid.uuid4().hex}")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.integration
class TestUserCascade:
    async def test_deleting_user_cascades_to_owned_records(self, db_session):
        user = await _create_user(db_session)
        account = FinancialAccountModel(
            user_id=user.id, name="Cuenta", account_type="bank", currency_code="DOP"
        )
        db_session.add(account)
        await db_session.flush()

        tx = TransactionModel(
            user_id=user.id,
            account_id=account.id,
            transaction_type="expense",
            amount=Decimal("100.0000"),
            currency_code="DOP",
            description="test",
            effective_date=date(2026, 1, 2),
        )
        recurring = TransactionRecurringModel(
            user_id=user.id,
            account_id=account.id,
            transaction_type="expense",
            amount=Decimal("50.0000"),
            currency_code="DOP",
            description="recur",
            frequency="monthly",
            start_date=date(2026, 1, 1),
            next_execution_date=date(2026, 2, 1),
        )
        notification = NotificationModel(
            user_id=user.id,
            channel="in_app",
            type="info",
            title="hola",
            body="mundo",
        )
        telegram_code = TelegramLinkCodeModel(
            user_id=user.id, code="123456", expires_at=datetime.now(UTC)
        )
        db_session.add_all([tx, recurring, notification, telegram_code])
        await db_session.commit()

        user_id = user.id
        await db_session.delete(user)
        await db_session.commit()

        assert await _count(db_session, FinancialAccountModel, user_id=user_id) == 0
        assert await _count(db_session, TransactionModel, user_id=user_id) == 0
        assert await _count(db_session, TransactionRecurringModel, user_id=user_id) == 0
        assert await _count(db_session, NotificationModel, user_id=user_id) == 0
        assert await _count(db_session, TelegramLinkCodeModel, user_id=user_id) == 0

    async def test_deleting_user_removes_telegram_link_codes(self, db_session):
        user = await _create_user(db_session)
        telegram_code = TelegramLinkCodeModel(
            user_id=user.id, code="654321", expires_at=datetime.now(UTC)
        )
        db_session.add(telegram_code)
        await db_session.commit()

        user_id = user.id
        await db_session.delete(user)
        await db_session.commit()

        assert await _count(db_session, TelegramLinkCodeModel, user_id=user_id) == 0


@pytest.mark.integration
class TestAccountCascade:
    async def test_deleting_account_nullifies_transactions_and_cascades_children(self, db_session):
        user = await _create_user(db_session)
        account = FinancialAccountModel(
            user_id=user.id, name="Cuenta", account_type="bank", currency_code="DOP"
        )
        db_session.add(account)
        await db_session.flush()

        tx = TransactionModel(
            user_id=user.id,
            account_id=account.id,
            transaction_type="expense",
            amount=Decimal("100.0000"),
            currency_code="DOP",
            description="test",
            effective_date=date(2026, 1, 2),
        )
        debit_card = DebitCardModel(user_id=user.id, account_id=account.id, name="Debito")
        wallet = WalletModel(user_id=user.id, name="Billetera", wallet_type="personal")
        db_session.add_all([tx, debit_card, wallet])
        await db_session.flush()

        wallet_account = WalletAccountModel(wallet_id=wallet.id, account_id=account.id)
        income_schedule = IncomeScheduleModel(
            user_id=user.id,
            description="sueldo",
            amount=Decimal("1000.0000"),
            currency_code="DOP",
            account_id=account.id,
            expected_date=date(2026, 1, 31),
        )
        db_session.add_all([wallet_account, income_schedule])
        await db_session.commit()

        account_id = account.id
        tx_id = tx.id
        wallet_id = wallet.id
        await db_session.delete(account)
        await db_session.commit()
        db_session.expire_all()

        remaining = (
            await db_session.execute(select(TransactionModel).where(TransactionModel.id == tx_id))
        ).scalar_one()
        assert remaining is not None
        assert remaining.account_id is None
        assert await _count(db_session, DebitCardModel, account_id=account_id) == 0
        assert await _count(db_session, WalletAccountModel, account_id=account_id) == 0
        assert await _count(db_session, IncomeScheduleModel, account_id=account_id) == 0
        assert await _count(db_session, WalletModel, id=wallet_id) == 1

        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.integration
class TestTransactionCascade:
    async def test_deleting_transaction_cascades_to_children(self, db_session):
        user = await _create_user(db_session)
        account = FinancialAccountModel(
            user_id=user.id, name="Cuenta", account_type="bank", currency_code="DOP"
        )
        db_session.add(account)
        await db_session.flush()

        tx = TransactionModel(
            user_id=user.id,
            account_id=account.id,
            transaction_type="income",
            amount=Decimal("1000.0000"),
            currency_code="DOP",
            description="sueldo",
            effective_date=date(2026, 1, 2),
        )
        db_session.add(tx)
        await db_session.flush()

        tag = TransactionTagModel(transaction_id=tx.id, user_id=user.id, tag_name="vital")
        attachment = TransactionAttachmentModel(
            transaction_id=tx.id,
            user_id=user.id,
            filename="r.png",
            original_filename="recibo.png",
            mime_type="image/png",
            file_size=123,
            storage_path="receipts/r.png",
        )
        audit_log = TransactionAuditLogModel(
            transaction_id=tx.id, user_id=user.id, action="created"
        )
        income = IncomeModel(
            user_id=user.id,
            transaction_id=tx.id,
            income_type="salary",
            effective_date=date(2026, 1, 2),
        )
        db_session.add_all([tag, attachment, audit_log, income])
        await db_session.commit()

        tx_id = tx.id
        await db_session.delete(tx)
        await db_session.commit()

        assert await _count(db_session, TransactionTagModel, transaction_id=tx_id) == 0
        assert await _count(db_session, TransactionAttachmentModel, transaction_id=tx_id) == 0
        assert await _count(db_session, TransactionAuditLogModel, transaction_id=tx_id) == 0
        assert await _count(db_session, IncomeModel, transaction_id=tx_id) == 0

        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.integration
class TestCategoryCascade:
    async def test_deleting_category_cascades_subcategories_and_nullifies_transactions(
        self, db_session
    ):
        user = await _create_user(db_session)
        category = CategoryModel(user_id=user.id, name="Comida", category_type="expense")
        db_session.add(category)
        await db_session.flush()

        subcategory = SubcategoryModel(category_id=category.id, name="Restaurantes")
        tx = TransactionModel(
            user_id=user.id,
            transaction_type="expense",
            amount=Decimal("50.0000"),
            currency_code="DOP",
            description="almuerzo",
            effective_date=date(2026, 1, 2),
            category_id=category.id,
            subcategory_id=subcategory.id,
        )
        db_session.add_all([subcategory, tx])
        await db_session.commit()

        category_id = category.id
        tx_id = tx.id
        await db_session.delete(category)
        await db_session.commit()
        db_session.expire_all()

        assert await _count(db_session, SubcategoryModel, category_id=category_id) == 0
        remaining = (
            await db_session.execute(select(TransactionModel).where(TransactionModel.id == tx_id))
        ).scalar_one()
        assert remaining is not None
        assert remaining.category_id is None
        assert remaining.subcategory_id is None

        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.integration
class TestCreditCardCascade:
    async def test_deleting_credit_card_nullifies_transactions_and_cascades_card_children(
        self, db_session
    ):
        user = await _create_user(db_session)
        card = CreditCardModel(user_id=user.id, name="Visa")
        db_session.add(card)
        await db_session.flush()

        tx = TransactionModel(
            user_id=user.id,
            transaction_type="expense",
            amount=Decimal("200.0000"),
            currency_code="DOP",
            description="compra",
            effective_date=date(2026, 1, 2),
            credit_card_id=card.id,
        )
        alert = CardAlertModel(
            user_id=user.id,
            credit_card_id=card.id,
            alert_type="limit",
            title="limite",
            message="cerca del limite",
        )
        spending_limit = CardSpendingLimitModel(
            user_id=user.id,
            credit_card_id=card.id,
            limit_type="monthly",
            limit_amount=Decimal("5000.0000"),
        )
        db_session.add_all([tx, alert, spending_limit])
        await db_session.commit()

        card_id = card.id
        tx_id = tx.id
        await db_session.delete(card)
        await db_session.commit()
        db_session.expire_all()

        assert await _count(db_session, CardAlertModel, credit_card_id=card_id) == 0
        assert await _count(db_session, CardSpendingLimitModel, credit_card_id=card_id) == 0
        remaining = (
            await db_session.execute(select(TransactionModel).where(TransactionModel.id == tx_id))
        ).scalar_one()
        assert remaining is not None
        assert remaining.credit_card_id is None

        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.integration
class TestGoalCascade:
    async def test_deleting_goal_cascades_milestones(self, db_session):
        user = await _create_user(db_session)
        goal = FinancialGoalModel(
            user_id=user.id,
            name="Viaje",
            target_amount=Decimal("100000.0000"),
            current_amount=Decimal("0.0000"),
            start_date=date(2026, 1, 1),
            target_date=date(2027, 1, 1),
        )
        db_session.add(goal)
        await db_session.flush()

        milestone = GoalMilestoneModel(
            goal_id=goal.id,
            user_id=user.id,
            event_type="progress",
            amount_at_event=Decimal("25000.0000"),
            target_amount=Decimal("100000.0000"),
            pct_complete=Decimal("0.2500"),
        )
        db_session.add(milestone)
        await db_session.commit()

        goal_id = goal.id
        await db_session.delete(goal)
        await db_session.commit()

        assert await _count(db_session, GoalMilestoneModel, goal_id=goal_id) == 0

        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.integration
class TestBudgetAlertCascade:
    async def test_deleting_budget_cascades_alerts(self, db_session):
        user = await _create_user(db_session)
        from app.infrastructure.models.budget import BudgetModel

        budget = BudgetModel(
            user_id=user.id,
            name="Comida",
            budget_type="monthly",
            amount=Decimal("5000.0000"),
            period="monthly",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
        db_session.add(budget)
        await db_session.flush()

        alert = BudgetAlertModel(
            user_id=user.id,
            budget_id=budget.id,
            alert_type="threshold",
            title="alerta",
            message="usado 80%",
            threshold_percentage=80,
        )
        db_session.add(alert)
        await db_session.commit()

        budget_id = budget.id
        await db_session.delete(budget)
        await db_session.commit()

        assert await _count(db_session, BudgetAlertModel, budget_id=budget_id) == 0

        await db_session.delete(user)
        await db_session.commit()
