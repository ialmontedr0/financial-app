from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.credit_purchase import CreditPurchaseModel
from app.infrastructure.models.credit_purchase_installment import CreditPurchaseInstallmentModel

logger = structlog.get_logger()


class CreditPurchaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, **kwargs: object) -> CreditPurchaseModel:
        purchase = CreditPurchaseModel(user_id=user_id, **kwargs)
        self._session.add(purchase)
        await self._session.flush()
        logger.info("credit_purchase_created", id=str(purchase.id), user_id=str(user_id))
        return purchase

    async def get(self, purchase_id: uuid.UUID, user_id: uuid.UUID) -> CreditPurchaseModel | None:
        stmt = select(CreditPurchaseModel).where(
            CreditPurchaseModel.id == purchase_id,
            CreditPurchaseModel.user_id == user_id,
            CreditPurchaseModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, user_id: uuid.UUID, status: str | None = None
    ) -> list[CreditPurchaseModel]:
        filters = [
            CreditPurchaseModel.user_id == user_id,
            CreditPurchaseModel.deleted_at.is_(None),
        ]
        if status:
            filters.append(CreditPurchaseModel.status == status)
        stmt = (
            select(CreditPurchaseModel)
            .where(and_(*filters))
            .order_by(CreditPurchaseModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self, purchase: CreditPurchaseModel, **kwargs: object
    ) -> CreditPurchaseModel:
        for key, value in kwargs.items():
            setattr(purchase, key, value)
        await self._session.flush()
        await self._session.refresh(purchase)
        return purchase

    async def delete(self, purchase: CreditPurchaseModel) -> bool:
        purchase.deleted_at = datetime.now(datetime.UTC)
        await self._session.flush()
        logger.info("credit_purchase_deleted", id=str(purchase.id))
        return True

    async def create_installments(
        self, purchase_id: uuid.UUID, installments: list[dict]
    ) -> list[CreditPurchaseInstallmentModel]:
        models = []
        for inst in installments:
            model = CreditPurchaseInstallmentModel(purchase_id=purchase_id, **inst)
            self._session.add(model)
            models.append(model)
        await self._session.flush()
        return models

    async def list_installments(
        self, purchase_id: uuid.UUID
    ) -> list[CreditPurchaseInstallmentModel]:
        stmt = (
            select(CreditPurchaseInstallmentModel)
            .where(CreditPurchaseInstallmentModel.purchase_id == purchase_id)
            .order_by(CreditPurchaseInstallmentModel.installment_number)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_installment(
        self, installment_id: uuid.UUID
    ) -> CreditPurchaseInstallmentModel | None:
        stmt = select(CreditPurchaseInstallmentModel).where(
            CreditPurchaseInstallmentModel.id == installment_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_installment_paid(
        self, installment_id: uuid.UUID, paid_date: date | None = None
    ) -> CreditPurchaseInstallmentModel | None:

        stmt = select(CreditPurchaseInstallmentModel).where(
            CreditPurchaseInstallmentModel.id == installment_id
        )
        result = await self._session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry:
            entry.status = "paid"
            entry.paid_at = paid_date or datetime.now(UTC).date()
            await self._session.flush()
        return entry
