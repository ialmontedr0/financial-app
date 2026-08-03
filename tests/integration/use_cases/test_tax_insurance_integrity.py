"""Integrity tests for tax and insurance FK ON DELETE behaviour.

These tests hard-delete parents through the ORM and assert the database-level
ON DELETE CASCADE / SET NULL rules keep referential integrity intact.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.infrastructure.models.insurance import InsuranceModel
from app.infrastructure.models.insurance_policy import InsurancePolicyModel
from app.infrastructure.models.insurance_premium import InsurancePremiumModel
from app.infrastructure.models.tax_category import TaxCategoryModel
from app.infrastructure.models.tax_deduction import TaxDeductionModel
from app.infrastructure.models.user import UserModel


def _unique_email() -> str:
    return f"tax-ins-{uuid.uuid4().hex[:12]}@example.com"


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
class TestTaxCascade:
    async def test_deleting_user_cascades_tax_records(self, db_session):
        user = await _create_user(db_session)
        category = TaxCategoryModel(user_id=user.id, name="Salud", tax_year=2025)
        db_session.add(category)
        await db_session.flush()

        deduction = TaxDeductionModel(
            user_id=user.id,
            category_id=category.id,
            description="Prima médica",
            amount=Decimal("1200.0000"),
            date=date(2025, 4, 10),
            tax_year=2025,
        )
        db_session.add(deduction)
        await db_session.commit()

        user_id = user.id
        await db_session.delete(user)
        await db_session.commit()

        assert await _count(db_session, TaxCategoryModel, user_id=user_id) == 0
        assert await _count(db_session, TaxDeductionModel, user_id=user_id) == 0

    async def test_deleting_category_nullifies_deductions(self, db_session):
        user = await _create_user(db_session)
        category = TaxCategoryModel(user_id=user.id, name="Educación", tax_year=2025)
        db_session.add(category)
        await db_session.flush()

        deduction = TaxDeductionModel(
            user_id=user.id,
            category_id=category.id,
            description="Matrícula",
            amount=Decimal("900.0000"),
            date=date(2025, 8, 1),
            tax_year=2025,
        )
        db_session.add(deduction)
        await db_session.commit()

        deduction_id = deduction.id
        await db_session.delete(category)
        await db_session.commit()
        db_session.expire_all()

        remaining = (
            await db_session.execute(
                select(TaxDeductionModel).where(TaxDeductionModel.id == deduction_id)
            )
        ).scalar_one()
        assert remaining is not None
        assert remaining.category_id is None

        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.integration
class TestInsuranceCascade:
    async def test_deleting_user_cascades_insurances(self, db_session):
        user = await _create_user(db_session)
        insurance = InsuranceModel(
            user_id=user.id,
            name="Seguro Auto",
            type="auto",
            status="active",
            start_date=date(2026, 1, 1),
            premium_amount=Decimal("1200.0000"),
            premium_frequency="annual",
        )
        db_session.add(insurance)
        await db_session.flush()

        policy = InsurancePolicyModel(
            insurance_id=insurance.id, name="Colisión", deductible=Decimal("500.0000")
        )
        premium = InsurancePremiumModel(
            insurance_id=insurance.id,
            amount=Decimal("100.0000"),
            due_date=date(2026, 2, 1),
            status="pending",
        )
        db_session.add_all([policy, premium])
        await db_session.commit()

        user_id = user.id
        await db_session.delete(user)
        await db_session.commit()

        assert await _count(db_session, InsuranceModel, user_id=user_id) == 0

    async def test_deleting_insurance_cascades_policies_and_premiums(self, db_session):
        user = await _create_user(db_session)
        insurance = InsuranceModel(
            user_id=user.id,
            name="Seguro Salud",
            type="health",
            status="active",
            start_date=date(2026, 1, 1),
            premium_amount=Decimal("3000.0000"),
            premium_frequency="monthly",
        )
        db_session.add(insurance)
        await db_session.flush()

        policy = InsurancePolicyModel(insurance_id=insurance.id, name="Hospitalario")
        premium = InsurancePremiumModel(
            insurance_id=insurance.id,
            amount=Decimal("250.0000"),
            due_date=date(2026, 1, 15),
            status="pending",
        )
        db_session.add_all([policy, premium])
        await db_session.commit()

        insurance_id = insurance.id
        await db_session.delete(insurance)
        await db_session.commit()
        db_session.expire_all()

        assert await _count(db_session, InsurancePolicyModel, insurance_id=insurance_id) == 0
        assert await _count(db_session, InsurancePremiumModel, insurance_id=insurance_id) == 0

        await db_session.delete(user)
        await db_session.commit()
