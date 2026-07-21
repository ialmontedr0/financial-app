from fastapi import APIRouter

from app.api.v1.accounts.router import router as accounts_router
from app.api.v1.analytics.router import router as analytics_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.budgets.router import router as budgets_router
from app.api.v1.cards.router import router as cards_router
from app.api.v1.categories.router import router as categories_router
from app.api.v1.expenses.router import router as expenses_router
from app.api.v1.goals.router import router as goals_router
from app.api.v1.incomes.router import router as incomes_router
from app.api.v1.loans.router import router as loans_router
from app.api.v1.transactions.router import router as transactions_router
from app.api.v1.users.router import router as users_router
from app.api.v1.wallets.router import router as wallets_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(wallets_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(incomes_router)
api_v1_router.include_router(expenses_router)
api_v1_router.include_router(goals_router)
api_v1_router.include_router(budgets_router)
api_v1_router.include_router(cards_router)
api_v1_router.include_router(loans_router)
api_v1_router.include_router(analytics_router)
