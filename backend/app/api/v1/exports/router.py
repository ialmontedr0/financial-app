"""Export API endpoints — CSV, Excel, PDF, Calendar (.ics)."""

from __future__ import annotations

import contextlib
import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/exports", tags=["Exports"])


async def _query_transactions(
    db: AsyncSession,
    user_id: uuid.UUID,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    transaction_type: str | None = None,
    account_id: str | None = None,
) -> list[dict[str, Any]]:
    """Query transactions with filters and return as dicts."""
    from datetime import date as date_type

    from app.infrastructure.models.category import CategoryModel
    from app.infrastructure.models.transaction import TransactionModel

    query = select(TransactionModel).where(
        TransactionModel.user_id == user_id,
        TransactionModel.deleted_at.is_(None),
    )

    if date_from:
        try:
            d = date_type.fromisoformat(date_from)
            query = query.where(TransactionModel.effective_date >= d)
        except ValueError:
            pass
    if date_to:
        try:
            d = date_type.fromisoformat(date_to)
            query = query.where(TransactionModel.effective_date <= d)
        except ValueError:
            pass
    if transaction_type:
        query = query.where(TransactionModel.transaction_type == transaction_type)
    if account_id:
        with contextlib.suppress(ValueError):
            query = query.where(TransactionModel.account_id == uuid.UUID(account_id))
    if category:
        cat_q = select(CategoryModel.id).where(
            CategoryModel.name.ilike(f"%{category}%"),
            CategoryModel.user_id.in_([user_id, None]),
        )
        cat_result = await db.execute(cat_q)
        cat_ids = [r[0] for r in cat_result.all()]
        if cat_ids:
            query = query.where(TransactionModel.category_id.in_(cat_ids))

    query = query.order_by(TransactionModel.effective_date.desc())
    result = await db.execute(query)
    txs = result.scalars().all()

    return [
        {
            "date": str(tx.effective_date),
            "description": tx.description,
            "amount": float(tx.amount),
            "type": tx.transaction_type,
            "category": tx.category.name if tx.category else "",
            "account": tx.account.name if tx.account else "",
            "currency": tx.currency_code,
            "notes": tx.notes or "",
        }
        for tx in txs
    ]


@router.get("/transactions/csv")
async def export_transactions_csv(
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    category: str | None = Query(None),
    transaction_type: str | None = Query(None),
    account_id: str | None = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export transactions as CSV file."""
    user_id = uuid.UUID(current_user["sub"])
    transactions = await _query_transactions(
        db, user_id, date_from, date_to, category, transaction_type, account_id
    )

    from app.integrations.csv_handler import transactions_to_csv

    csv_content = transactions_to_csv(transactions)

    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.get("/transactions/excel")
async def export_transactions_excel(
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    category: str | None = Query(None),
    transaction_type: str | None = Query(None),
    account_id: str | None = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export transactions as Excel file."""
    user_id = uuid.UUID(current_user["sub"])
    transactions = await _query_transactions(
        db, user_id, date_from, date_to, category, transaction_type, account_id
    )

    from app.integrations.excel_handler import transactions_to_excel

    excel_bytes = transactions_to_excel(transactions)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=transactions.xlsx"},
    )


@router.get("/transactions/pdf")
async def export_transactions_pdf(
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    category: str | None = Query(None),
    transaction_type: str | None = Query(None),
    account_id: str | None = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export transactions as PDF report."""
    user_id = uuid.UUID(current_user["sub"])
    transactions = await _query_transactions(
        db, user_id, date_from, date_to, category, transaction_type, account_id
    )

    from app.integrations.pdf_generator import generate_transaction_report

    pdf_bytes = generate_transaction_report(
        transactions,
        title="Transaction Report",
        user_email=current_user.get("email", ""),
        date_from=date_from or "",
        date_to=date_to or "",
    )

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=transactions_report.pdf"},
    )


@router.get("/budgets/pdf")
async def export_budgets_pdf(
    month: int | None = Query(None),
    year: int | None = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export budget report as PDF."""
    user_id = uuid.UUID(current_user["sub"])

    from app.infrastructure.models.budget import BudgetModel

    query = select(BudgetModel).where(BudgetModel.user_id == user_id)
    result = await db.execute(query)
    budgets = result.scalars().all()

    budget_data = [
        {
            "category": b.category.name if b.category else str(b.category_id),
            "budget_amount": float(b.amount),
            "spent_amount": float(b.spent),
        }
        for b in budgets
    ]

    from app.integrations.pdf_generator import generate_budget_report

    pdf_bytes = generate_budget_report(budget_data)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=budget_report.pdf"},
    )


@router.get("/goals/pdf")
async def export_goals_pdf(
    status: str | None = Query(None),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export goals report as PDF."""
    user_id = uuid.UUID(current_user["sub"])

    from app.infrastructure.models.financial_goal import FinancialGoalModel

    query = select(FinancialGoalModel).where(FinancialGoalModel.user_id == user_id)
    if status and status != "all":
        query = query.where(FinancialGoalModel.status == status)

    result = await db.execute(query)
    goals = result.scalars().all()

    goal_data = [
        {
            "name": g.name,
            "target_amount": float(g.target_amount),
            "current_amount": float(g.current_amount),
            "status": g.status,
            "target_date": str(g.target_date),
        }
        for g in goals
    ]

    from app.integrations.pdf_generator import generate_goals_report

    pdf_bytes = generate_goals_report(goal_data)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=goals_report.pdf"},
    )


@router.get("/calendar/recurring")
async def export_recurring_calendar(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export recurring transactions as ICS calendar file."""
    from app.infrastructure.models.transaction_recurring import TransactionRecurringModel

    user_id = uuid.UUID(current_user["sub"])
    result = await db.execute(
        select(TransactionRecurringModel).where(
            TransactionRecurringModel.user_id == user_id,
            TransactionRecurringModel.is_active == True,  # noqa: E712
        )
    )
    recurring = result.scalars().all()

    recurring_data = [
        {
            "description": r.description,
            "amount": float(r.amount),
            "currency": r.currency_code,
            "type": r.transaction_type,
            "frequency": r.frequency,
            "next_execution_date": str(r.next_execution_date),
            "category": "",
            "account": "",
        }
        for r in recurring
    ]

    from app.integrations.calendar_handler import recurring_transactions_to_ics

    ics_content = recurring_transactions_to_ics(recurring_data, current_user.get("email", ""))

    return StreamingResponse(
        io.StringIO(ics_content),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=recurring_transactions.ics"},
    )


@router.get("/calendar/goals")
async def export_goals_calendar(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Export financial goals as ICS calendar file (deadlines + reminders)."""
    from app.infrastructure.models.financial_goal import FinancialGoalModel

    user_id = uuid.UUID(current_user["sub"])
    result = await db.execute(
        select(FinancialGoalModel).where(FinancialGoalModel.user_id == user_id)
    )
    goals = result.scalars().all()

    goal_data = [
        {
            "name": g.name,
            "target_amount": float(g.target_amount),
            "current_amount": float(g.current_amount),
            "target_date": str(g.target_date),
            "status": g.status,
            "progress_pct": (
                float(g.current_amount) / float(g.target_amount) * 100
                if float(g.target_amount) > 0
                else 0
            ),
        }
        for g in goals
    ]

    from app.integrations.calendar_handler import goals_to_ics

    ics_content = goals_to_ics(goal_data, current_user.get("email", ""))

    return StreamingResponse(
        io.StringIO(ics_content),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=financial_goals.ics"},
    )
