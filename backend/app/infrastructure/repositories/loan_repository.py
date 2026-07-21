"""Loan repository — all database operations for loans."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.loan import LoanModel
from app.infrastructure.models.loan_amortization_entry import LoanAmortizationEntryModel
from app.infrastructure.models.loan_payment import LoanPaymentModel

logger = structlog.get_logger()


class LoanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── LOAN CRUD ──────────────────────────────────────────────

    async def create_loan(self, user_id: uuid.UUID, **kwargs: object) -> LoanModel:
        loan = LoanModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(loan)
        await self._session.flush()
        logger.info("loan_created", loan_id=str(loan.id), user_id=str(user_id))
        return loan

    async def get_loan(self, loan_id: uuid.UUID, user_id: uuid.UUID) -> LoanModel | None:
        stmt = select(LoanModel).where(
            LoanModel.id == loan_id,
            LoanModel.user_id == user_id,
            LoanModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_loans(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        loan_type: str | None = None,
    ) -> list[LoanModel]:
        filters = [
            LoanModel.user_id == user_id,
            LoanModel.deleted_at.is_(None),
        ]
        if status:
            filters.append(LoanModel.status == status)
        if loan_type:
            filters.append(LoanModel.loan_type == loan_type)

        stmt = select(LoanModel).where(and_(*filters)).order_by(LoanModel.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_loan(self, loan: LoanModel, **kwargs: object) -> LoanModel:
        for key, value in kwargs.items():
            setattr(loan, key, value)
        await self._session.flush()
        await self._session.refresh(loan)
        logger.info("loan_updated", loan_id=str(loan.id))
        return loan

    async def delete_loan(self, loan: LoanModel) -> bool:
        loan.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("loan_deleted", loan_id=str(loan.id))
        return True

    # ── PAYMENTS ───────────────────────────────────────────────

    async def create_payment(self, loan_id: uuid.UUID, **kwargs: object) -> LoanPaymentModel:
        payment = LoanPaymentModel(loan_id=loan_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(payment)
        await self._session.flush()
        logger.info("loan_payment_created", payment_id=str(payment.id), loan_id=str(loan_id))
        return payment

    async def list_payments(
        self, loan_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[LoanPaymentModel]:
        stmt = (
            select(LoanPaymentModel)
            .where(LoanPaymentModel.loan_id == loan_id)
            .order_by(LoanPaymentModel.payment_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_last_payment(self, loan_id: uuid.UUID) -> LoanPaymentModel | None:
        stmt = (
            select(LoanPaymentModel)
            .where(
                LoanPaymentModel.loan_id == loan_id,
                LoanPaymentModel.status == "completed",
            )
            .order_by(LoanPaymentModel.payment_date.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_payments_summary(self, loan_id: uuid.UUID) -> dict:
        stmt = select(
            func.coalesce(func.sum(LoanPaymentModel.amount), 0).label("total_paid"),
            func.coalesce(func.sum(LoanPaymentModel.interest_portion), 0).label("total_interest"),
            func.coalesce(func.sum(LoanPaymentModel.principal_portion), 0).label("total_principal"),
            func.coalesce(func.sum(LoanPaymentModel.penalty_portion), 0).label("total_penalties"),
            func.count(LoanPaymentModel.id).label("payment_count"),
        ).where(
            LoanPaymentModel.loan_id == loan_id,
            LoanPaymentModel.status == "completed",
        )
        result = await self._session.execute(stmt)
        row = result.one()
        return {
            "total_paid": float(row.total_paid),
            "total_interest": float(row.total_interest),
            "total_principal": float(row.total_principal),
            "total_penalties": float(row.total_penalties),
            "payment_count": row.payment_count,
        }

    # ── AMORTIZATION ENTRIES ───────────────────────────────────

    async def create_amortization_entries(
        self, loan_id: uuid.UUID, entries: list[dict]
    ) -> list[LoanAmortizationEntryModel]:
        models = []
        for entry in entries:
            model = LoanAmortizationEntryModel(loan_id=loan_id, **entry)  # type: ignore[arg-type]
            self._session.add(model)
            models.append(model)
        await self._session.flush()
        logger.info("amortization_entries_created", loan_id=str(loan_id), count=len(entries))
        return models

    async def list_amortization_entries(
        self, loan_id: uuid.UUID
    ) -> list[LoanAmortizationEntryModel]:
        stmt = (
            select(LoanAmortizationEntryModel)
            .where(LoanAmortizationEntryModel.loan_id == loan_id)
            .order_by(LoanAmortizationEntryModel.entry_number)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_entry_paid(self, entry_id: uuid.UUID) -> None:
        stmt = select(LoanAmortizationEntryModel).where(LoanAmortizationEntryModel.id == entry_id)
        result = await self._session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry:
            entry.is_paid = True
            await self._session.flush()

    async def delete_amortization_entries(self, loan_id: uuid.UUID) -> None:
        stmt = select(LoanAmortizationEntryModel).where(
            LoanAmortizationEntryModel.loan_id == loan_id
        )
        result = await self._session.execute(stmt)
        for entry in result.scalars().all():
            await self._session.delete(entry)
        await self._session.flush()

    # ── SUMMARY ────────────────────────────────────────────────

    async def get_loans_summary(self, user_id: uuid.UUID) -> dict:
        stmt = select(
            func.coalesce(func.sum(LoanModel.current_balance), 0).label("total_balance"),
            func.coalesce(func.sum(LoanModel.monthly_payment), 0).label("total_monthly_payment"),
            func.coalesce(func.sum(LoanModel.total_paid), 0).label("total_paid"),
            func.coalesce(func.sum(LoanModel.total_interest_paid), 0).label("total_interest_paid"),
            func.count(LoanModel.id).label("total_loans"),
        ).where(
            LoanModel.user_id == user_id,
            LoanModel.deleted_at.is_(None),
            LoanModel.status.in_(["active", "pending"]),
        )
        result = await self._session.execute(stmt)
        row = result.one()

        # count by status
        status_stmt = (
            select(LoanModel.status, func.count(LoanModel.id))
            .where(
                LoanModel.user_id == user_id,
                LoanModel.deleted_at.is_(None),
            )
            .group_by(LoanModel.status)
        )
        status_result = await self._session.execute(status_stmt)
        status_counts = {r[0]: r[1] for r in status_result.all()}

        return {
            "total_balance": float(row.total_balance),
            "total_monthly_payment": float(row.total_monthly_payment),
            "total_paid": float(row.total_paid),
            "total_interest_paid": float(row.total_interest_paid),
            "total_loans": row.total_loans,
            "by_status": status_counts,
        }

    async def get_upcoming_payments(self, user_id: uuid.UUID, days_ahead: int = 30) -> list[dict]:
        from datetime import timedelta

        cutoff = date.today() + timedelta(days=days_ahead)  # noqa: DTZ011
        stmt = (
            select(LoanModel)
            .where(
                LoanModel.user_id == user_id,
                LoanModel.deleted_at.is_(None),
                LoanModel.status == "active",
                LoanModel.next_payment_date.isnot(None),
                LoanModel.next_payment_date <= cutoff,
            )
            .order_by(LoanModel.next_payment_date)
        )
        result = await self._session.execute(stmt)
        loans = result.scalars().all()
        return [
            {
                "loan_id": str(loan.id),
                "loan_name": loan.name,
                "next_payment_date": loan.next_payment_date.isoformat()
                if loan.next_payment_date
                else None,
                "monthly_payment": float(loan.monthly_payment),
                "current_balance": float(loan.current_balance),
            }
            for loan in loans
        ]
