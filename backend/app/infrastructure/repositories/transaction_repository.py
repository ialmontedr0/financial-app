"""Repository for transaction persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import and_, func, select

from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.transaction import TransactionModel
from app.infrastructure.models.transaction_attachment import TransactionAttachmentModel
from app.infrastructure.models.transaction_audit_log import TransactionAuditLogModel
from app.infrastructure.models.transaction_recurring import TransactionRecurringModel
from app.infrastructure.models.transaction_tag import TransactionTagModel

if TYPE_CHECKING:
    import uuid
    from datetime import date
    from decimal import Decimal

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ==============================================================
    # Transactions CRUD
    # ==============================================================

    async def create(self, user_id: uuid.UUID, **kwargs: object) -> TransactionModel:
        tx = TransactionModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(tx)
        await self._session.flush()
        logger.info("transaction_created", user_id=str(user_id), tx_id=str(tx.id), tx_type=tx.transaction_type, amount=str(tx.amount))
        return tx

    async def get_by_id(self, tx_id: uuid.UUID, user_id: uuid.UUID) -> TransactionModel | None:
        stmt = select(TransactionModel).where(
            TransactionModel.id == tx_id, TransactionModel.user_id == user_id, TransactionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: uuid.UUID, *, transaction_type: str | None = None, status: str | None = None,
        category_id: uuid.UUID | None = None, subcategory_id: uuid.UUID | None = None,
        account_id: uuid.UUID | None = None, tag: str | None = None,
        min_amount: Decimal | None = None, max_amount: Decimal | None = None,
        date_from: date | None = None, date_to: date | None = None,
        source: str | None = None, search: str | None = None,
        transfer_id: uuid.UUID | None = None,
        sort_by: str = "effective_date", sort_order: str = "desc",
        page: int = 1, page_size: int = 20,
    ) -> tuple[list[TransactionModel], int]:
        base_stmt = select(TransactionModel).where(
            TransactionModel.user_id == user_id, TransactionModel.deleted_at.is_(None),
        )
        if transaction_type:
            base_stmt = base_stmt.where(TransactionModel.transaction_type == transaction_type)
        if status:
            base_stmt = base_stmt.where(TransactionModel.status == status)
        if category_id:
            base_stmt = base_stmt.where(TransactionModel.category_id == category_id)
        if subcategory_id:
            base_stmt = base_stmt.where(TransactionModel.subcategory_id == subcategory_id)
        if account_id:
            base_stmt = base_stmt.where(TransactionModel.account_id == account_id)
        if transfer_id:
            base_stmt = base_stmt.where(TransactionModel.transfer_id == transfer_id)
        if source:
            base_stmt = base_stmt.where(TransactionModel.source == source)
        if min_amount is not None:
            base_stmt = base_stmt.where(TransactionModel.amount >= min_amount)
        if max_amount is not None:
            base_stmt = base_stmt.where(TransactionModel.amount <= max_amount)
        if date_from:
            base_stmt = base_stmt.where(TransactionModel.effective_date >= date_from)
        if date_to:
            base_stmt = base_stmt.where(TransactionModel.effective_date <= date_to)
        if search:
            base_stmt = base_stmt.where(TransactionModel.description.ilike(f"%{search}%"))
        if tag:
            tag_subq = select(TransactionTagModel.transaction_id).where(
                TransactionTagModel.user_id == user_id, TransactionTagModel.tag_name == tag,
            ).scalar_subquery()
            base_stmt = base_stmt.where(TransactionModel.id.in_(tag_subq))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar() or 0

        sort_col = getattr(TransactionModel, sort_by, TransactionModel.effective_date)
        base_stmt = base_stmt.order_by(sort_col.asc() if sort_order == "asc" else sort_col.desc())
        offset = (page - 1) * page_size
        base_stmt = base_stmt.offset(offset).limit(page_size)

        result = await self._session.execute(base_stmt)
        return list(result.scalars().all()), total

    async def update(self, tx_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> TransactionModel | None:
        tx = await self.get_by_id(tx_id, user_id)
        if tx is None:
            return None
        for key, value in kwargs.items():
            if hasattr(tx, key):
                setattr(tx, key, value)
        await self._session.flush()
        await self._session.refresh(tx)
        logger.info("transaction_updated", user_id=str(user_id), tx_id=str(tx_id), fields=list(kwargs.keys()))
        return tx

    async def soft_delete(self, tx_id: uuid.UUID, user_id: uuid.UUID) -> TransactionModel | None:
        from datetime import UTC, datetime
        return await self.update(tx_id, user_id, deleted_at=datetime.now(UTC), status="cancelled")

    # ==============================================================
    # Account Balance
    # ==============================================================

    async def update_account_balance(self, account_id: uuid.UUID, amount: Decimal, operation: str) -> FinancialAccountModel | None:
        stmt = select(FinancialAccountModel).where(FinancialAccountModel.id == account_id)
        result = await self._session.execute(stmt)
        account = result.scalar_one_or_none()
        if account is None:
            return None
        if operation == "add":
            account.balance = account.balance + amount  # type: ignore[assignment]
        elif operation == "subtract":
            account.balance = account.balance - amount  # type: ignore[assignment]
        await self._session.flush()
        await self._session.refresh(account)
        return account

    async def get_account_by_id(self, account_id: uuid.UUID, user_id: uuid.UUID) -> FinancialAccountModel | None:
        stmt = select(FinancialAccountModel).where(
            FinancialAccountModel.id == account_id, FinancialAccountModel.user_id == user_id,
            FinancialAccountModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ==============================================================
    # Summary
    # ==============================================================

    async def get_summary(self, user_id: uuid.UUID, date_from: date, date_to: date) -> dict:
        from decimal import Decimal

        base_filter = and_(
            TransactionModel.user_id == user_id, TransactionModel.deleted_at.is_(None),
            TransactionModel.effective_date >= date_from, TransactionModel.effective_date <= date_to,
        )
        stmt = select(
            TransactionModel.transaction_type,
            func.count(TransactionModel.id).label("count"),
            func.sum(TransactionModel.amount).label("total"),
        ).where(base_filter).group_by(TransactionModel.transaction_type)
        result = await self._session.execute(stmt)
        rows = result.all()

        by_type: dict[str, dict] = {}
        for row in rows:
            by_type[row.transaction_type] = {"count": row.count, "total": str(row.total or 0)}

        total_income = Decimal(by_type.get("income", {}).get("total", "0"))
        total_expenses = Decimal(by_type.get("expense", {}).get("total", "0"))
        return {
            "period_start": date_from.isoformat(), "period_end": date_to.isoformat(),
            "total_income": str(total_income), "total_expenses": str(total_expenses),
            "net_flow": str(total_income - total_expenses),
            "total_income_count": by_type.get("income", {}).get("count", 0),
            "total_expense_count": by_type.get("expense", {}).get("count", 0),
            "total_transfer_count": by_type.get("transfer", {}).get("count", 0),
            "total_adjustment_count": by_type.get("adjustment", {}).get("count", 0),
            "by_type": by_type,
        }

    # ==============================================================
    # Tags
    # ==============================================================

    async def add_tags(self, tx_id: uuid.UUID, user_id: uuid.UUID, tag_names: list[str]) -> list[TransactionTagModel]:
        existing_stmt = select(TransactionTagModel.tag_name).where(
            TransactionTagModel.transaction_id == tx_id, TransactionTagModel.tag_name.in_(tag_names),
        )
        existing_result = await self._session.execute(existing_stmt)
        existing = {row[0] for row in existing_result.all()}
        added: list[TransactionTagModel] = []
        for tag in tag_names:
            tag_clean = tag.strip().lower()
            if tag_clean and tag_clean not in existing:
                tag_model = TransactionTagModel(transaction_id=tx_id, user_id=user_id, tag_name=tag_clean)
                self._session.add(tag_model)
                added.append(tag_model)
        if added:
            await self._session.flush()
            logger.info("tags_added", tx_id=str(tx_id), tags=[t.tag_name for t in added])
        return added

    async def remove_tag(self, tx_id: uuid.UUID, tag_name: str) -> bool:
        stmt = select(TransactionTagModel).where(
            TransactionTagModel.transaction_id == tx_id, TransactionTagModel.tag_name == tag_name.strip().lower(),
        )
        result = await self._session.execute(stmt)
        tag = result.scalar_one_or_none()
        if tag is None:
            return False
        await self._session.delete(tag)
        await self._session.flush()
        return True

    async def get_tags(self, tx_id: uuid.UUID) -> list[TransactionTagModel]:
        stmt = select(TransactionTagModel).where(
            TransactionTagModel.transaction_id == tx_id
        ).order_by(TransactionTagModel.tag_name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ==============================================================
    # Attachments
    # ==============================================================

    async def create_attachment(self, tx_id: uuid.UUID, user_id: uuid.UUID, **kwargs: str | int) -> TransactionAttachmentModel:
        att = TransactionAttachmentModel(transaction_id=tx_id, user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(att)
        await self._session.flush()
        logger.info("attachment_created", tx_id=str(tx_id), filename=att.original_filename)
        return att

    async def list_attachments(self, tx_id: uuid.UUID) -> list[TransactionAttachmentModel]:
        stmt = select(TransactionAttachmentModel).where(
            TransactionAttachmentModel.transaction_id == tx_id, TransactionAttachmentModel.deleted_at.is_(None),
        ).order_by(TransactionAttachmentModel.created_at.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_attachment(self, attachment_id: uuid.UUID) -> TransactionAttachmentModel | None:
        stmt = select(TransactionAttachmentModel).where(
            TransactionAttachmentModel.id == attachment_id, TransactionAttachmentModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_attachment(self, attachment_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime
        att = await self.get_attachment(attachment_id)
        if att is None:
            return False
        att.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return True

    # ==============================================================
    # Recurring
    # ==============================================================

    async def create_recurring(self, user_id: uuid.UUID, **kwargs: object) -> TransactionRecurringModel:
        rec = TransactionRecurringModel(user_id=user_id, **kwargs)  # type: ignore[arg-type]
        self._session.add(rec)
        await self._session.flush()
        logger.info("recurring_created", user_id=str(user_id), recurring_id=str(rec.id), frequency=rec.frequency)
        return rec

    async def get_recurring_by_id(self, recurring_id: uuid.UUID, user_id: uuid.UUID) -> TransactionRecurringModel | None:
        stmt = select(TransactionRecurringModel).where(
            TransactionRecurringModel.id == recurring_id, TransactionRecurringModel.user_id == user_id,
            TransactionRecurringModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_recurring(self, user_id: uuid.UUID, *, is_active: bool | None = None) -> list[TransactionRecurringModel]:
        stmt = select(TransactionRecurringModel).where(
            TransactionRecurringModel.user_id == user_id, TransactionRecurringModel.deleted_at.is_(None),
        )
        if is_active is not None:
            stmt = stmt.where(TransactionRecurringModel.is_active == is_active)
        stmt = stmt.order_by(TransactionRecurringModel.next_execution_date.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_recurring(self, recurring_id: uuid.UUID, user_id: uuid.UUID, **kwargs: object) -> TransactionRecurringModel | None:
        rec = await self.get_recurring_by_id(recurring_id, user_id)
        if rec is None:
            return None
        for key, value in kwargs.items():
            if hasattr(rec, key):
                setattr(rec, key, value)
        await self._session.flush()
        await self._session.refresh(rec)
        return rec

    async def soft_delete_recurring(self, recurring_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        from datetime import UTC, datetime
        rec = await self.get_recurring_by_id(recurring_id, user_id)
        if rec is None:
            return False
        rec.deleted_at = datetime.now(UTC)
        rec.is_active = False
        await self._session.flush()
        return True

    async def get_due_recurring(self) -> list[TransactionRecurringModel]:
        from datetime import date as date_type
        stmt = select(TransactionRecurringModel).where(
            TransactionRecurringModel.is_active.is_(True), TransactionRecurringModel.deleted_at.is_(None),
            TransactionRecurringModel.next_execution_date <= date_type.today(),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ==============================================================
    # Audit Log
    # ==============================================================

    async def create_audit_log(self, tx_id: uuid.UUID, user_id: uuid.UUID, action: str,
        changes: dict | None = None, ip_address: str | None = None, user_agent: str | None = None,
    ) -> TransactionAuditLogModel:
        log = TransactionAuditLogModel(
            transaction_id=tx_id, user_id=user_id, action=action, changes=changes,
            ip_address=ip_address, user_agent=user_agent,
        )
        self._session.add(log)
        await self._session.flush()
        logger.info("audit_log_created", tx_id=str(tx_id), action=action)
        return log

    async def get_audit_log(self, tx_id: uuid.UUID) -> list[TransactionAuditLogModel]:
        stmt = select(TransactionAuditLogModel).where(
            TransactionAuditLogModel.transaction_id == tx_id
        ).order_by(TransactionAuditLogModel.created_at.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
