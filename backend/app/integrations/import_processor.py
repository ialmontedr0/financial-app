"""Transaction import orchestrator — validates, maps, and inserts transactions."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.import_job import ImportJobModel

logger = structlog.get_logger()


async def process_import(
    db: AsyncSession,
    user_id: uuid.UUID,
    transactions: list[dict[str, Any]],
    job: ImportJobModel,
) -> dict[str, Any]:
    """Process validated transactions: map categories, create records."""
    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.financial_account import FinancialAccountModel
    from app.infrastructure.models.transaction import TransactionModel

    cat_result = await db.execute(
        select(CategoryModel).where(
            CategoryModel.user_id.in_([user_id, None]),
            CategoryModel.is_active == True,  # noqa: E712
        )
    )
    categories = {c.name.lower(): c for c in cat_result.scalars().all()}

    acct_result = await db.execute(
        select(FinancialAccountModel).where(
            FinancialAccountModel.user_id == user_id,
            FinancialAccountModel.status == "active",
        )
    )
    accounts = {a.name.lower(): a for a in acct_result.scalars().all()}

    valid_count = 0
    error_count = 0
    errors: list[dict[str, Any]] = []

    for idx, tx_data in enumerate(transactions):
        try:
            try:
                effective_date = date.fromisoformat(tx_data["date"])
            except (ValueError, TypeError):
                try:
                    effective_date = datetime.strptime(tx_data["date"], "%m/%d/%Y").date()  # noqa: DTZ007
                except (ValueError, TypeError):
                    try:
                        effective_date = datetime.strptime(tx_data["date"], "%d/%m/%Y").date()  # noqa: DTZ007
                    except (ValueError, TypeError):
                        errors.append({
                            "row": idx + 1,
                            "field": "date",
                            "message": f"Cannot parse date: {tx_data['date']}",
                        })
                        error_count += 1
                        continue

            category_id = None
            if tx_data.get("category"):
                cat = categories.get(tx_data["category"].lower())
                if cat:
                    category_id = cat.id

            account_id = None
            if tx_data.get("account"):
                acct = accounts.get(tx_data["account"].lower())
                if acct:
                    account_id = acct.id

            currency = tx_data.get("currency", "DOP") or "DOP"

            transaction = TransactionModel(
                user_id=user_id,
                account_id=account_id or uuid.UUID(int=0),
                category_id=category_id,
                transaction_type=tx_data.get("type", "expense"),
                amount=tx_data["amount"],
                currency_code=currency,
                description=tx_data["description"],
                notes=tx_data.get("notes"),
                effective_date=effective_date,
                status="completed",
                source="import",
            )

            if not account_id:
                if accounts:
                    account_id = next(iter(accounts.values())).id
                    transaction.account_id = account_id
                else:
                    errors.append({"row": idx + 1, "field": "account", "message": "No account found"})
                    error_count += 1
                    continue

            db.add(transaction)
            valid_count += 1

        except Exception as e:
            errors.append({"row": idx + 1, "field": "general", "message": str(e)})
            error_count += 1

    job.processed_rows = len(transactions)
    job.valid_rows = valid_count
    job.error_rows = error_count
    job.errors = errors if errors else None
    job.status = "completed"
    job.completed_at = datetime.now(UTC)

    await db.flush()

    logger.info(
        "import_processed",
        job_id=str(job.id),
        total=len(transactions),
        valid=valid_count,
        errors=error_count,
    )

    return {
        "total": len(transactions),
        "valid": valid_count,
        "errors": error_count,
        "error_details": errors,
    }
