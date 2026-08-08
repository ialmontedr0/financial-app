"""Repository for LentLoan (préstamo otorgado) persistence."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.lent_loan import LentLoanModel, LentLoanPaymentModel

logger = structlog.get_logger()


class LentLoanRepository:
    """CRUD operations for lent loans and their received payments."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: uuid.UUID, **kwargs: Any) -> LentLoanModel:
        loan = LentLoanModel(user_id=user_id, **kwargs)
        self._session.add(loan)
        await self._session.flush()
        return loan

    async def get(self, lent_loan_id: uuid.UUID, user_id: uuid.UUID) -> LentLoanModel | None:
        stmt = select(LentLoanModel).where(
            LentLoanModel.id == lent_loan_id,
            LentLoanModel.user_id == user_id,
            LentLoanModel.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[LentLoanModel]:
        stmt = select(LentLoanModel).where(
            LentLoanModel.user_id == user_id,
            LentLoanModel.deleted_at.is_(None),
        )
        if status:
            stmt = stmt.where(LentLoanModel.status == status)
        stmt = stmt.order_by(LentLoanModel.created_at.desc()).offset(skip).limit(limit)
        return list((await self._session.execute(stmt)).scalars().all())

    async def update(self, loan: LentLoanModel, **kwargs: Any) -> LentLoanModel:
        for key, value in kwargs.items():
            if hasattr(loan, key):
                setattr(loan, key, value)
        await self._session.flush()
        await self._session.refresh(loan)
        return loan

    async def soft_delete(self, loan: LentLoanModel, now) -> None:
        await self._session.execute(
            update(LentLoanModel).where(LentLoanModel.id == loan.id).values(deleted_at=now)
        )
        await self._session.flush()

    async def add_payment(
        self, lent_loan_id: uuid.UUID, user_id: uuid.UUID, **kwargs: Any
    ) -> LentLoanPaymentModel:
        payment = LentLoanPaymentModel(
            lent_loan_id=lent_loan_id, user_id=user_id, **kwargs
        )
        self._session.add(payment)
        await self._session.flush()
        return payment

    async def list_payments(self, lent_loan_id: uuid.UUID) -> list[LentLoanPaymentModel]:
        stmt = (
            select(LentLoanPaymentModel)
            .where(
                LentLoanPaymentModel.lent_loan_id == lent_loan_id,
                LentLoanPaymentModel.deleted_at.is_(None),
            )
            .order_by(LentLoanPaymentModel.received_date.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def payments_summary(self, lent_loan_id: uuid.UUID) -> dict:
        payments = await self.list_payments(lent_loan_id)
        total = sum(float(p.amount) for p in payments)
        principal = sum(float(p.principal_portion) for p in payments)
        interest = sum(float(p.interest_portion) for p in payments)
        return {
            "total_received": total,
            "principal_received": principal,
            "interest_received": interest,
            "payments": len(payments),
            "last_payment_date": max((p.received_date for p in payments), default=None),
        }

    async def get_portfolio_summary(self, user_id: uuid.UUID) -> dict:
        """Aggregate figures for the investment portfolio equivalent."""
        stmt = select(LentLoanModel).where(
            LentLoanModel.user_id == user_id,
            LentLoanModel.deleted_at.is_(None),
            LentLoanModel.status.in_(["active", "defaulted"]),
        )
        loans = list((await self._session.execute(stmt)).scalars().all())
        total_outstanding = sum(
            float(loan.current_balance * Decimal("1")) for loan in loans
        )
        total_principal = sum(float(loan.principal_amount) for loan in loans)
        total_received = sum(float(loan.total_received) for loan in loans)
        total_interest_expected = sum(
            float(loan.total_interest_expected) for loan in loans
        )
        return {
            "count": len(loans),
            "total_outstanding": total_outstanding,
            "total_principal": total_principal,
            "total_received": total_received,
            "total_interest_expected": total_interest_expected,
        }

    async def list_receivables(self, user_id: uuid.UUID) -> list[LentLoanModel]:
        """Prestamos otorgados pendientes de cobro (cuentas por cobrar).

        Ordena primero los vencidos (defaulted) y luego por fecha de próxima
        cuota ascendente para priorizar los cobros más urgentes.
        """
        stmt = select(LentLoanModel).where(
            LentLoanModel.user_id == user_id,
            LentLoanModel.deleted_at.is_(None),
            LentLoanModel.status.in_(["active", "defaulted"]),
        )
        stmt = stmt.order_by(
            case((LentLoanModel.status == "defaulted", 0), else_=1),
            LentLoanModel.next_payment_date.asc().nullslast(),
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_total_receivables(self, user_id: uuid.UUID) -> Decimal:
        """Suma del saldo pendiente de los prestamos otorgados (cuentas por cobrar)."""
        stmt = select(func.coalesce(func.sum(LentLoanModel.current_balance), 0)).where(
            LentLoanModel.user_id == user_id,
            LentLoanModel.deleted_at.is_(None),
            LentLoanModel.status.in_(["active", "defaulted"]),
        )
        return (await self._session.execute(stmt)).scalar_one()
