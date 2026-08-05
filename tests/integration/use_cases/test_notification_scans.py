"""Integration tests for scheduled notification scan use cases."""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.application.budgets.scan_budgets import ScanBudgetsUseCase
from app.application.expenses.scan_renewals import ScanSubscriptionRenewalsUseCase
from app.application.loans.scan_loan_due import ScanLoanDueUseCase
from app.infrastructure.models.loan import LoanModel
from app.infrastructure.models.notification import NotificationModel
from app.infrastructure.models.subscription import SubscriptionModel
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.password_hasher import PasswordHasher


async def _create_user(db, email: str):
    user = await UserRepository(db).create(
        email=email, password_hash=PasswordHasher.hash_password("Test1234!")
    )
    await db.commit()
    return user


@pytest.mark.integration
class TestScanSubscriptionRenewals:
    async def test_notifies_subscription_near_renewal(self, db_session, test_password):
        user = await _create_user(db_session, "sub-notif@test.com")

        sub = SubscriptionModel(
            user_id=user.id,
            name="Netflix",
            amount=500,
            currency_code="DOP",
            billing_frequency="monthly",
            status="active",
            start_date=date.today() - timedelta(days=20),
            next_billing_date=date.today() + timedelta(days=3),
        )
        db_session.add(sub)
        await db_session.commit()

        result = await ScanSubscriptionRenewalsUseCase(db_session).execute()
        await db_session.commit()

        assert result["notified"] >= 1
        rows = await db_session.execute(
            select(NotificationModel).where(NotificationModel.user_id == user.id)
        )
        notif = rows.scalars().first()
        assert notif is not None
        assert notif.type == "bill_due"
        assert "Netflix" in notif.body
        assert notif.data["link"] == "/expenses/subscriptions"

    async def test_does_not_duplicate_notifications(self, db_session, test_password):
        user = await _create_user(db_session, "sub-notif2@test.com")

        sub = SubscriptionModel(
            user_id=user.id,
            name="Spotify",
            amount=300,
            currency_code="DOP",
            billing_frequency="monthly",
            status="active",
            start_date=date.today() - timedelta(days=10),
            next_billing_date=date.today() + timedelta(days=2),
        )
        db_session.add(sub)
        await db_session.commit()

        use_case = ScanSubscriptionRenewalsUseCase(db_session)
        await use_case.execute()
        await db_session.commit()
        await use_case.execute()
        await db_session.commit()

        rows = await db_session.execute(
            select(NotificationModel).where(
                NotificationModel.user_id == user.id,
                NotificationModel.type == "bill_due",
            )
        )
        assert len(rows.scalars().all()) == 1


@pytest.mark.integration
class TestScanLoanDue:
    async def test_notifies_loan_payment_due(self, db_session, test_password):
        user = await _create_user(db_session, "loan-notif@test.com")

        loan = LoanModel(
            user_id=user.id,
            name="Préstamo Auto",
            loan_type="auto",
            principal_amount=100000,
            current_balance=90000,
            annual_interest_rate=8,
            term_months=36,
            monthly_payment=3130,
            status="active",
            next_payment_date=date.today() + timedelta(days=2),
        )
        db_session.add(loan)
        await db_session.commit()

        result = await ScanLoanDueUseCase(db_session).execute()
        await db_session.commit()

        assert result["notified"] >= 1
        rows = await db_session.execute(
            select(NotificationModel).where(NotificationModel.user_id == user.id)
        )
        notif = rows.scalars().first()
        assert notif.type == "payment_due"
        assert notif.data["link"] == f"/loans/{loan.id}"


@pytest.mark.integration
class TestScanBudgets:
    async def test_scans_without_errors_when_no_budgets(self, db_session, test_password):
        await _create_user(db_session, "budget-scan@test.com")
        result = await ScanBudgetsUseCase(db_session).execute()
        await db_session.commit()
        assert "users_scanned" in result
