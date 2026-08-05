"""Full-text search endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, literal_column, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.infrastructure.models.category import CategoryModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.transaction import TransactionModel

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/transactions")
async def search_transactions(
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_id = uuid.UUID(current_user["sub"])
    query = text("websearch_to_tsquery('spanish', :q)")
    params = {"q": q}

    stmt = (
        select(
            TransactionModel,
            CategoryModel.name.label("category_name"),
            FinancialAccountModel.name.label("account_name"),
            func.ts_rank(TransactionModel.search_vector, query).label("rank"),
        )
        .outerjoin(CategoryModel, TransactionModel.category_id == CategoryModel.id)
        .outerjoin(
            FinancialAccountModel,
            TransactionModel.account_id == FinancialAccountModel.id,
        )
        .where(
            TransactionModel.user_id == user_id,
            TransactionModel.deleted_at.is_(None),
            TransactionModel.search_vector.op("@@")(query),
        )
        .order_by(literal_column("rank").desc())
        .offset(skip)
        .limit(limit)
    )

    count_stmt = (
        select(func.count(TransactionModel.id))
        .where(
            TransactionModel.user_id == user_id,
            TransactionModel.deleted_at.is_(None),
            TransactionModel.search_vector.op("@@")(query),
        )
    )

    result = await db.execute(stmt, params)
    total = (await db.execute(count_stmt, params)).scalar_one()

    items = [
        {
            "id": str(tx.id),
            "description": tx.description,
            "amount": str(tx.amount),
            "transaction_type": tx.transaction_type,
            "effective_date": tx.effective_date.isoformat() if tx.effective_date else None,
            "category_name": category_name,
            "account_name": account_name,
        }
        for tx, category_name, account_name, _rank in result.all()
    ]
    return {"results": items, "total": total}


@router.get("/suggestions")
async def search_suggestions(
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_id = uuid.UUID(current_user["sub"])

    # Categorías
    cat_stmt = select(CategoryModel.id, CategoryModel.name).where(
        CategoryModel.user_id == user_id,
        CategoryModel.name.ilike(f"%{q}%"),
    )
    cats = [
        {"type": "category", "id": str(cid), "label": name}
        for cid, name in (await db.execute(cat_stmt)).all()
    ]

    # Cuentas
    acc_stmt = select(FinancialAccountModel.id, FinancialAccountModel.name).where(
        FinancialAccountModel.user_id == user_id,
        FinancialAccountModel.name.ilike(f"%{q}%"),
    )
    accs = [
        {"type": "account", "id": str(aid), "label": name}
        for aid, name in (await db.execute(acc_stmt)).all()
    ]

    # Descripciones únicas de transacciones
    tx_stmt = (
        select(TransactionModel.description)
        .where(
            TransactionModel.user_id == user_id,
            TransactionModel.description.ilike(f"%{q}%"),
        )
        .distinct()
        .limit(8)
    )
    txs = [
        {"type": "transaction", "id": desc, "label": desc}
        for (desc,) in (await db.execute(tx_stmt)).all()
    ]

    return {"suggestions": [*cats, *accs, *txs][:12]}
