"""Gathers real financial context for the chat system prompt."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.infrastructure.repositories.account_repository import AccountRepository
from app.infrastructure.repositories.budget_repository import BudgetRepository
from app.infrastructure.repositories.goal_repository import GoalRepository
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession


async def build_financial_context(session: AsyncSession, user_id: uuid.UUID, today: date) -> dict:
    """Retora un dictado compacto de una captura financiera del usuario."""
    account_repo = AccountRepository(session)
    budget_repo = BudgetRepository(session)
    goal_repo = GoalRepository(session)
    tx_repo = TransactionRepository(session)

    accounts = await account_repo.list_by_user(user_id)
    budgets = await budget_repo.list_budgets(user_id, is_active=True)
    goals = await goal_repo.list_goals(user_id)
    recent, _ = await tx_repo.list_by_user(user_id, page_size=8)

    context = {
        "today": today.isoformat(),
        "accounts": [
            {
                "name": a.name,
                "balance": str(a.balance),
                "currency": getattr(a, "currency_code", None) or "MXN",
            }
            for a in accounts
        ],
        "budgets": [
            {
                "name": b.name,
                "amount": str(b.amount),
                "spent": str(b.spent),
                "pct_used": round(float(b.spent) / float(b.amount) * 100, 1)
                if float(b.amount) > 0
                else 0,
            }
            for b in budgets
        ],
        "goals": [
            {
                "name": g.name,
                "target_amount": str(g.target_amount),
                "progress_pct": round(float(g.current_amount) / float(g.target_amount) * 100, 1)
                if float(g.target_amount) > 0
                else 0,
            }
            for g in goals
        ],
        "recent_transactions": [
            {
                "date": t.effective_date.isoformat() if t.effective_date else None,
                "description": t.description,
                "amount": str(t.amount),
                "currency": getattr(t, "currency_code", None) or "MXN",
                "type": t.transaction_type,
            }
            for t in recent
        ],
    }
    return context
