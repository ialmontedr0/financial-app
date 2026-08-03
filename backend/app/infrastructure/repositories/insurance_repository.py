"""Insurance repository — all database operations for insurances, policies and premiums."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.insurance import InsuranceModel
from app.infrastructure.models.insurance_policy import InsurancePolicyModel
from app.infrastructure.models.insurance_premium import InsurancePremiumModel

logger = structlog.get_logger()

FREQUENCY_MONTHS = {
    "monthly": Decimal("1"),
    "quarterly": Decimal("3"),
    "semi_annual": Decimal("6"),
    "annual": Decimal("12"),
}


class InsuranceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── INSURANCE CRUD ────────────────────────────────────────

    async def create_insurance(self, user_id: uuid.UUID, **kwargs: object) -> InsuranceModel:
        insurance = InsuranceModel(user_id=user_id, **kwargs)
        self._session.add(insurance)
        await self._session.flush()
        logger.info("insurance_created", insurance_id=str(insurance.id), user_id=str(user_id))
        return insurance

    async def get_insurance(
        self, insurance_id: uuid.UUID, user_id: uuid.UUID
    ) -> InsuranceModel | None:
        stmt = select(InsuranceModel).where(
            InsuranceModel.id == insurance_id,
            InsuranceModel.user_id == user_id,
            InsuranceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_insurances(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        type: str | None = None,  # noqa: A002
    ) -> list[InsuranceModel]:
        filters = [
            InsuranceModel.user_id == user_id,
            InsuranceModel.deleted_at.is_(None),
        ]
        if status:
            filters.append(InsuranceModel.status == status)
        if type:
            filters.append(InsuranceModel.type == type)

        stmt = (
            select(InsuranceModel).where(and_(*filters)).order_by(InsuranceModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_insurance(self, insurance: InsuranceModel, **kwargs: object) -> InsuranceModel:
        for key, value in kwargs.items():
            setattr(insurance, key, value)
        await self._session.flush()
        await self._session.refresh(insurance)
        logger.info("insurance_updated", insurance_id=str(insurance.id))
        return insurance

    async def delete_insurance(self, insurance: InsuranceModel) -> bool:
        insurance.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("insurance_deleted", insurance_id=str(insurance.id))
        return True

    # ── POLICIES ──────────────────────────────────────────────

    async def create_policy(
        self, insurance_id: uuid.UUID, **kwargs: object
    ) -> InsurancePolicyModel:
        policy = InsurancePolicyModel(insurance_id=insurance_id, **kwargs)
        self._session.add(policy)
        await self._session.flush()
        logger.info(
            "insurance_policy_created", policy_id=str(policy.id), insurance_id=str(insurance_id)
        )
        return policy

    async def list_policies(self, insurance_id: uuid.UUID) -> list[InsurancePolicyModel]:
        stmt = (
            select(InsurancePolicyModel)
            .where(InsurancePolicyModel.insurance_id == insurance_id)
            .order_by(InsurancePolicyModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_policy(
        self, policy_id: uuid.UUID, insurance_id: uuid.UUID
    ) -> InsurancePolicyModel | None:
        stmt = select(InsurancePolicyModel).where(
            InsurancePolicyModel.id == policy_id,
            InsurancePolicyModel.insurance_id == insurance_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_policy(self, policy: InsurancePolicyModel) -> bool:
        await self._session.delete(policy)
        await self._session.flush()
        logger.info("insurance_policy_deleted", policy_id=str(policy.id))
        return True

    # ── PREMIUMS ──────────────────────────────────────────────

    async def create_premium(
        self, insurance_id: uuid.UUID, **kwargs: object
    ) -> InsurancePremiumModel:
        premium = InsurancePremiumModel(insurance_id=insurance_id, **kwargs)
        self._session.add(premium)
        await self._session.flush()
        logger.info(
            "insurance_premium_created", premium_id=str(premium.id), insurance_id=str(insurance_id)
        )
        return premium

    async def list_premiums(
        self,
        insurance_id: uuid.UUID,
        status: str | None = None,
    ) -> list[InsurancePremiumModel]:
        filters = [InsurancePremiumModel.insurance_id == insurance_id]
        if status:
            filters.append(InsurancePremiumModel.status == status)

        stmt = (
            select(InsurancePremiumModel)
            .where(and_(*filters))
            .order_by(InsurancePremiumModel.due_date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_premium(
        self, premium_id: uuid.UUID, insurance_id: uuid.UUID
    ) -> InsurancePremiumModel | None:
        stmt = select(InsurancePremiumModel).where(
            InsurancePremiumModel.id == premium_id,
            InsurancePremiumModel.insurance_id == insurance_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_premium(
        self, premium: InsurancePremiumModel, **kwargs: object
    ) -> InsurancePremiumModel:
        for key, value in kwargs.items():
            setattr(premium, key, value)
        await self._session.flush()
        await self._session.refresh(premium)
        logger.info("insurance_premium_updated", premium_id=str(premium.id))
        return premium

    async def delete_premium(self, premium: InsurancePremiumModel) -> bool:
        await self._session.delete(premium)
        await self._session.flush()
        logger.info("insurance_premium_deleted", premium_id=str(premium.id))
        return True

    # ── DASHBOARD ─────────────────────────────────────────────

    async def get_dashboard(self, user_id: uuid.UUID) -> dict[str, Any]:
        active_stmt = select(InsuranceModel).where(
            InsuranceModel.user_id == user_id,
            InsuranceModel.deleted_at.is_(None),
            InsuranceModel.status == "active",
        )
        active_result = await self._session.execute(active_stmt)
        active = list(active_result.scalars().all())

        total_monthly = Decimal("0")
        total_coverage = Decimal("0")
        for insurance in active:
            months = FREQUENCY_MONTHS.get(insurance.premium_frequency, Decimal("1"))
            if months:
                total_monthly += insurance.premium_amount / months
            total_coverage += insurance.coverage_amount or Decimal("0")

        today = date.today()  # noqa: DTZ011
        due_stmt = (
            select(InsurancePremiumModel)
            .join(InsuranceModel, InsuranceModel.id == InsurancePremiumModel.insurance_id)
            .where(
                InsuranceModel.user_id == user_id,
                InsuranceModel.deleted_at.is_(None),
                InsurancePremiumModel.status.in_(["pending", "overdue"]),
                InsurancePremiumModel.paid_date.is_(None),
                InsurancePremiumModel.due_date <= today,
            )
            .order_by(InsurancePremiumModel.due_date)
        )
        due_result = await self._session.execute(due_stmt)
        due_premiums = list(due_result.scalars().all())

        due_items = []
        for premium in due_premiums:
            due_items.append(
                {
                    "premium_id": str(premium.id),
                    "insurance_id": str(premium.insurance_id),
                    "amount": float(premium.amount),
                    "due_date": premium.due_date.isoformat(),
                    "status": premium.status,
                }
            )

        return {
            "active_policies": len(active),
            "total_monthly_premiums": float(total_monthly.quantize(Decimal("0.01"))),
            "due_premiums": len(due_premiums),
            "total_coverage": float(total_coverage.quantize(Decimal("0.01"))),
            "upcoming_premiums": due_items,
        }
