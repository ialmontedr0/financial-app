from fastapi import APIRouter

from app.api.v1.accounts.router import router as accounts_router
from app.api.v1.admin.router import router as admin_router
from app.api.v1.ai.router import router as ai_router
from app.api.v1.analytics.router import router as analytics_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.automations.router import router as automations_router
from app.api.v1.budgets.router import router as budgets_router
from app.api.v1.cards.router import router as cards_router
from app.api.v1.categories.router import router as categories_router
from app.api.v1.chat.router import router as chat_router
from app.api.v1.credit_purchases.router import router as credit_purchases_router
from app.api.v1.currency.router import router as currency_router
from app.api.v1.debit_cards.router import router as debit_cards_router
from app.api.v1.expenses.router import router as expenses_router
from app.api.v1.exports.router import router as exports_router
from app.api.v1.financial_data.router import router as financial_data_router
from app.api.v1.goals.router import router as goals_router
from app.api.v1.health.router import router as health_router
from app.api.v1.imports.router import router as imports_router
from app.api.v1.incomes.router import router as incomes_router
from app.api.v1.insurance.router import router as insurance_router
from app.api.v1.investments.router import router as investments_router
from app.api.v1.loans.router import router as loans_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.ocr.router import router as ocr_router
from app.api.v1.plaid.router import router as plaid_router
from app.api.v1.search.router import router as search_router
from app.api.v1.taxes.router import router as taxes_router
from app.api.v1.telegram.router import router as telegram_router
from app.api.v1.transactions.router import router as transactions_router
from app.api.v1.users.router import router as users_router
from app.api.v1.wallets.router import router as wallets_router

api_v1_router = APIRouter()

api_v1_router.include_router(admin_router)
api_v1_router.include_router(automations_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(wallets_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(imports_router)
api_v1_router.include_router(incomes_router)
api_v1_router.include_router(expenses_router)
api_v1_router.include_router(exports_router)
api_v1_router.include_router(financial_data_router)
api_v1_router.include_router(goals_router)
api_v1_router.include_router(budgets_router)
api_v1_router.include_router(cards_router)
api_v1_router.include_router(credit_purchases_router)
api_v1_router.include_router(currency_router)
api_v1_router.include_router(debit_cards_router)
api_v1_router.include_router(loans_router)
api_v1_router.include_router(insurance_router)
api_v1_router.include_router(investments_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(ocr_router)
api_v1_router.include_router(plaid_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(taxes_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(telegram_router)
api_v1_router.include_router(health_router)
