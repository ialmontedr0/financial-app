from app.infrastructure.models.ai_model_registry import AIModelRegistryModel
from app.infrastructure.models.ai_prediction import AIPredictionModel
from app.infrastructure.models.automation_execution_log import (
    AutomationExecutionLogModel,
)
from app.infrastructure.models.automation_rule import AutomationRuleModel
from app.infrastructure.models.budget import BudgetModel
from app.infrastructure.models.budget_alert import BudgetAlertModel
from app.infrastructure.models.card_alert import CardAlertModel
from app.infrastructure.models.card_spending_limit import CardSpendingLimitModel
from app.infrastructure.models.category import CategoryModel
from app.infrastructure.models.category_rule import CategoryRuleModel
from app.infrastructure.models.chat import ChatMessageModel, ChatSessionModel
from app.infrastructure.models.credit_card import CreditCardModel
from app.infrastructure.models.credit_card_bill import CreditCardBillModel
from app.infrastructure.models.credit_purchase import CreditPurchaseModel
from app.infrastructure.models.credit_purchase_installment import CreditPurchaseInstallmentModel
from app.infrastructure.models.currency_exchange_rate import CurrencyExchangeRateModel
from app.infrastructure.models.debit_card import DebitCardModel
from app.infrastructure.models.domain_event import DomainEventModel
from app.infrastructure.models.email_verification import EmailVerificationModel
from app.infrastructure.models.expense_service import ExpenseServiceModel
from app.infrastructure.models.expense_template import ExpenseTemplateModel
from app.infrastructure.models.financial_account import FinancialAccountModel
from app.infrastructure.models.financial_goal import FinancialGoalModel
from app.infrastructure.models.goal_milestone import GoalMilestoneModel
from app.infrastructure.models.goal_simulation import GoalSimulationModel
from app.infrastructure.models.idempotency_key import IdempotencyKeyModel
from app.infrastructure.models.import_job import ImportJobModel
from app.infrastructure.models.income import IncomeModel
from app.infrastructure.models.income_schedule import IncomeScheduleModel
from app.infrastructure.models.income_source import IncomeSourceModel
from app.infrastructure.models.insurance import InsuranceModel
from app.infrastructure.models.insurance_policy import InsurancePolicyModel
from app.infrastructure.models.insurance_premium import InsurancePremiumModel
from app.infrastructure.models.investment import (
    AssetModel,
    AssetPriceHistoryModel,
    InvestmentTransactionModel,
    PortfolioAssetModel,
    PortfolioModel,
)
from app.infrastructure.models.lent_loan import LentLoanModel, LentLoanPaymentModel
from app.infrastructure.models.loan import LoanModel
from app.infrastructure.models.loan_amortization_entry import LoanAmortizationEntryModel
from app.infrastructure.models.loan_payment import LoanPaymentModel
from app.infrastructure.models.login_attempt import LoginAttemptModel
from app.infrastructure.models.notification import NotificationModel
from app.infrastructure.models.notification_preference import NotificationPreferenceModel
from app.infrastructure.models.permission import PermissionModel
from app.infrastructure.models.plaid_item import PlaidItemModel
from app.infrastructure.models.role import RoleModel
from app.infrastructure.models.role_permission import RolePermissionModel
from app.infrastructure.models.subcategory import SubcategoryModel
from app.infrastructure.models.subscription import SubscriptionModel
from app.infrastructure.models.system_audit_log import SystemAuditLogModel
from app.infrastructure.models.tax_category import TaxCategoryModel
from app.infrastructure.models.tax_deduction import TaxDeductionModel
from app.infrastructure.models.telegram_link_code import TelegramLinkCodeModel
from app.infrastructure.models.transaction import TransactionModel
from app.infrastructure.models.transaction_attachment import TransactionAttachmentModel
from app.infrastructure.models.transaction_audit_log import TransactionAuditLogModel
from app.infrastructure.models.transaction_recurring import TransactionRecurringModel
from app.infrastructure.models.transaction_tag import TransactionTagModel
from app.infrastructure.models.user import UserModel
from app.infrastructure.models.user_preference import UserPreferenceModel
from app.infrastructure.models.user_profile import UserProfileModel
from app.infrastructure.models.user_session import UserSessionModel
from app.infrastructure.models.wallet import WalletModel
from app.infrastructure.models.wallet_account import WalletAccountModel

__all__ = [
    "AIModelRegistryModel",
    "AIPredictionModel",
    "AssetModel",
    "AssetPriceHistoryModel",
    "AutomationExecutionLogModel",
    "AutomationRuleModel",
    "BudgetAlertModel",
    "BudgetModel",
    "CardAlertModel",
    "CardSpendingLimitModel",
    "CategoryModel",
    "CategoryRuleModel",
    "ChatMessageModel",
    "ChatSessionModel",
    "CreditCardBillModel",
    "CreditCardModel",
    "CreditPurchaseInstallmentModel",
    "CreditPurchaseModel",
    "CurrencyExchangeRateModel",
    "DebitCardModel",
    "DomainEventModel",
    "EmailVerificationModel",
    "ExpenseServiceModel",
    "ExpenseTemplateModel",
    "FinancialAccountModel",
    "FinancialGoalModel",
    "GoalMilestoneModel",
    "GoalSimulationModel",
    "IdempotencyKeyModel",
    "ImportJobModel",
    "IncomeModel",
    "IncomeScheduleModel",
    "IncomeSourceModel",
    "InsuranceModel",
    "InsurancePolicyModel",
    "InsurancePremiumModel",
    "InvestmentTransactionModel",
    "LentLoanModel",
    "LentLoanPaymentModel",
    "LoanAmortizationEntryModel",
    "LoanModel",
    "LoanPaymentModel",
    "LoginAttemptModel",
    "NotificationModel",
    "NotificationPreferenceModel",
    "PermissionModel",
    "PlaidItemModel",
    "PortfolioAssetModel",
    "PortfolioModel",
    "RoleModel",
    "RolePermissionModel",
    "SubcategoryModel",
    "SubscriptionModel",
    "SystemAuditLogModel",
    "TaxCategoryModel",
    "TaxDeductionModel",
    "TelegramLinkCodeModel",
    "TransactionAttachmentModel",
    "TransactionAuditLogModel",
    "TransactionModel",
    "TransactionRecurringModel",
    "TransactionTagModel",
    "UserModel",
    "UserPreferenceModel",
    "UserProfileModel",
    "UserSessionModel",
    "WalletAccountModel",
    "WalletModel",
]
