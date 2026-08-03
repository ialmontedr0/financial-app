"""Tax repository — all database operations for tax categories and deductions."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.tax_category import TaxCategoryModel
from app.infrastructure.models.tax_deduction import TaxDeductionModel

logger = structlog.get_logger()

UNCATEGORIZED_LABEL = "Sin categoría"


class TaxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── CATEGORIES ────────────────────────────────────────────

    async def create_category(self, user_id: uuid.UUID, **kwargs: object) -> TaxCategoryModel:
        category = TaxCategoryModel(user_id=user_id, **kwargs)
        self._session.add(category)
        await self._session.flush()
        logger.info("tax_category_created", category_id=str(category.id), user_id=str(user_id))
        return category

    async def get_category(
        self, category_id: uuid.UUID, user_id: uuid.UUID
    ) -> TaxCategoryModel | None:
        stmt = select(TaxCategoryModel).where(
            TaxCategoryModel.id == category_id,
            TaxCategoryModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_categories(
        self, user_id: uuid.UUID, tax_year: int | None = None
    ) -> list[TaxCategoryModel]:
        filters = [TaxCategoryModel.user_id == user_id]
        if tax_year:
            filters.append(TaxCategoryModel.tax_year == tax_year)

        stmt = (
            select(TaxCategoryModel)
            .where(and_(*filters))
            .order_by(TaxCategoryModel.tax_year.desc(), TaxCategoryModel.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def delete_category(self, category: TaxCategoryModel) -> bool:
        await self._session.delete(category)
        await self._session.flush()
        logger.info("tax_category_deleted", category_id=str(category.id))
        return True

    # ── DEDUCTIONS ────────────────────────────────────────────

    async def create_deduction(self, user_id: uuid.UUID, **kwargs: object) -> TaxDeductionModel:
        deduction = TaxDeductionModel(user_id=user_id, **kwargs)
        self._session.add(deduction)
        await self._session.flush()
        logger.info("tax_deduction_created", deduction_id=str(deduction.id), user_id=str(user_id))
        return deduction

    async def get_deduction(
        self, deduction_id: uuid.UUID, user_id: uuid.UUID
    ) -> TaxDeductionModel | None:
        stmt = select(TaxDeductionModel).where(
            TaxDeductionModel.id == deduction_id,
            TaxDeductionModel.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_deductions(
        self,
        user_id: uuid.UUID,
        tax_year: int | None = None,
        category_id: uuid.UUID | None = None,
    ) -> list[TaxDeductionModel]:
        filters = [TaxDeductionModel.user_id == user_id]
        if tax_year:
            filters.append(TaxDeductionModel.tax_year == tax_year)
        if category_id:
            filters.append(TaxDeductionModel.category_id == category_id)

        stmt = (
            select(TaxDeductionModel).where(and_(*filters)).order_by(TaxDeductionModel.date.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_deduction(
        self, deduction: TaxDeductionModel, **kwargs: object
    ) -> TaxDeductionModel:
        for key, value in kwargs.items():
            setattr(deduction, key, value)
        await self._session.flush()
        await self._session.refresh(deduction)
        logger.info("tax_deduction_updated", deduction_id=str(deduction.id))
        return deduction

    async def delete_deduction(self, deduction: TaxDeductionModel) -> bool:
        await self._session.delete(deduction)
        await self._session.flush()
        logger.info("tax_deduction_deleted", deduction_id=str(deduction.id))
        return True

    # ── SUMMARY ───────────────────────────────────────────────

    async def get_tax_summary(self, user_id: uuid.UUID, tax_year: int) -> dict[str, Any]:
        base = [
            TaxDeductionModel.user_id == user_id,
            TaxDeductionModel.tax_year == tax_year,
        ]

        totals_stmt = select(
            func.coalesce(func.sum(TaxDeductionModel.amount), 0).label("total_amount"),
            func.coalesce(func.sum(TaxDeductionModel.deductible), 0).label("total_deductible"),
            func.count(TaxDeductionModel.id).label("deduction_count"),
        ).where(and_(*base))
        totals_row = (await self._session.execute(totals_stmt)).one()

        by_category_stmt = (
            select(
                func.coalesce(TaxCategoryModel.name, UNCATEGORIZED_LABEL).label("category_name"),
                func.coalesce(func.sum(TaxDeductionModel.amount), 0).label("total"),
            )
            .select_from(TaxDeductionModel)
            .outerjoin(TaxCategoryModel, TaxDeductionModel.category_id == TaxCategoryModel.id)
            .where(and_(*base))
            .group_by(TaxCategoryModel.name)
            .order_by(func.sum(TaxDeductionModel.amount).desc())
        )
        by_category_result = await self._session.execute(by_category_stmt)
        by_category = [
            {"category": row.category_name, "total": float(row.total)}
            for row in by_category_result.all()
        ]

        return {
            "year": tax_year,
            "total_deductions": float(totals_row.total_amount),
            "total_deductible": float(totals_row.total_deductible),
            "deduction_count": totals_row.deduction_count,
            "by_category": by_category,
        }
