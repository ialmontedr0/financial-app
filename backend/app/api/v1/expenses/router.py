"""Expense management endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user, get_db

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/expenses", tags=["Expenses"])


# ======================================================================
# Expense CRUD
# ======================================================================


@router.post("", status_code=201)
async def create_expense(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from datetime import date as date_type

    from app.application.expenses.create_expense import CreateExpenseUseCase

    effective_date = (
        date_type.fromisoformat(body["effective_date"])
        if isinstance(body.get("effective_date"), str)
        else body.get("effective_date")
    )
    return await CreateExpenseUseCase(db).execute(
        user_id=uuid.UUID(current_user["sub"]),
        account_id=body["account_id"],
        amount=body["amount"],
        currency_code=body.get("currency_code", "DOP"),
        description=body["description"],
        effective_date=effective_date,
        category_id=body.get("category_id"),
        subcategory_id=body.get("subcategory_id"),
        status=body.get("status", "completed"),
        notes=body.get("notes"),
        source=body.get("source", "manual"),
        tags=body.get("tags"),
        template_id=body.get("template_id"),
        service_id=body.get("service_id"),
        subscription_id=body.get("subscription_id"),
        credit_card_id=body.get("credit_card_id"),
        priority=body.get("priority", "normal"),
    )


@router.post("/bulk", status_code=201)
async def create_expense_bulk(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.expenses.create_expense_bulk import CreateExpenseBulkUseCase

    return await CreateExpenseBulkUseCase(db).execute(
        uuid.UUID(current_user["sub"]), body["expenses"]
    )


@router.post("/split", status_code=201)
async def create_expense_split(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from datetime import date as date_type

    from app.application.expenses.create_expense_split import CreateExpenseSplitUseCase

    effective_date = (
        date_type.fromisoformat(body["effective_date"])
        if isinstance(body.get("effective_date"), str)
        else body.get("effective_date")
    )
    return await CreateExpenseSplitUseCase(db).execute(
        user_id=uuid.UUID(current_user["sub"]),
        account_id=body["account_id"],
        total_amount=body["total_amount"],
        currency_code=body.get("currency_code", "DOP"),
        description=body["description"],
        effective_date=effective_date,
        splits=body["splits"],
        notes=body.get("notes"),
        tags=body.get("tags"),
    )


@router.get("")
async def list_expenses(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
    status: str | None = Query(None),
    category_id: str | None = Query(None),
    subcategory_id: str | None = Query(None),
    account_id: str | None = Query(None),
    tag: str | None = Query(None),
    min_amount: float | None = Query(None),
    max_amount: float | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    source: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("effective_date"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    from datetime import date as date_type

    from app.application.expenses.list_expenses import ListExpensesUseCase

    d_from = date_type.fromisoformat(date_from) if date_from else None
    d_to = date_type.fromisoformat(date_to) if date_to else None
    return await ListExpensesUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        status=status,
        category_id=category_id,
        subcategory_id=subcategory_id,
        account_id=account_id,
        tag=tag,
        min_amount=min_amount,
        max_amount=max_amount,
        date_from=d_from,
        date_to=d_to,
        source=source,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/dashboard")
async def get_expense_dashboard(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
    date_from: str = Query(...),
    date_to: str = Query(...),
) -> dict:
    from datetime import date as date_type

    from app.application.expenses.get_expense_dashboard import GetExpenseDashboardUseCase

    return await GetExpenseDashboardUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        date_from=date_type.fromisoformat(date_from),
        date_to=date_type.fromisoformat(date_to),
    )


@router.get("/patterns")
async def get_spending_patterns(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.get_spending_patterns import GetSpendingPatternsUseCase

    return await GetSpendingPatternsUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/duplicates")
async def detect_duplicates(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
    days: int = Query(30, ge=1, le=365),
) -> dict:
    from app.application.expenses.detect_duplicates import DetectDuplicatesUseCase

    return await DetectDuplicatesUseCase(db).execute(uuid.UUID(current_user["sub"]), days=days)


@router.get("/recurring-candidates")
async def detect_recurring_candidates(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.detect_recurring import DetectRecurringUseCase

    return await DetectRecurringUseCase(db).execute(uuid.UUID(current_user["sub"]))


# ======================================================================
# Templates
# ======================================================================


@router.post("/templates", status_code=201)
async def create_template(
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db),# noqa: B008
) -> dict:
    from app.application.expenses.create_template import CreateTemplateUseCase

    return await CreateTemplateUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        name=body["name"],
        default_amount=float(body["amount"]) if body.get("amount") else 0,
        default_category_id=body.get("category_id") or None,
        default_subcategory_id=body.get("subcategory_id") or None,
        default_account_id=body.get("account_id") or None,
        default_notes=body.get("notes"),
    )


@router.get("/templates")
async def list_templates(
    current_user: dict = Depends(get_current_active_user),# noqa: B008
    db: AsyncSession = Depends(get_db),# noqa: B008
) -> dict:
    from app.application.expenses.list_templates import ListTemplatesUseCase

    return await ListTemplatesUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.post("/templates/{template_id}/create-expense", status_code=201)
async def create_from_template(
    template_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),# noqa: B008
    db: AsyncSession = Depends(get_db),# noqa: B008
) -> dict:
    from datetime import date as date_type

    from app.application.expenses.create_from_template import CreateFromTemplateUseCase

    effective_date = (
        date_type.fromisoformat(body["effective_date"])
        if isinstance(body.get("effective_date"), str)
        else body.get("effective_date")
    )
    return await CreateFromTemplateUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        template_id,
        account_id=body.get("account_id"),
        amount=body.get("amount"),
        effective_date=effective_date,
        notes=body.get("notes"),
        tags=body.get("tags"),
    )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.delete_template import DeleteTemplateUseCase

    return await DeleteTemplateUseCase(db).execute(uuid.UUID(current_user["sub"]), template_id)


# ======================================================================
# Services
# ======================================================================


@router.post("/services", status_code=201)
async def create_service(
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.create_service import CreateServiceUseCase

    return await CreateServiceUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        name=body["name"],
        service_type=body.get("service_type"),
        provider_name=body.get("provider"),
        account_number=body.get("account_number"),
        category_id=body.get("category_id"),
        due_day=body.get("due_day"),
        estimated_amount=float(body.get("estimated_amount") or body.get("amount") or 0) or None,
        notes=body.get("notes"),
    )


@router.get("/services")
async def list_services(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
    service_type: str | None = Query(None),
) -> dict:
    from app.application.expenses.list_services import ListServicesUseCase

    return await ListServicesUseCase(db).execute(
        uuid.UUID(current_user["sub"]), service_type=service_type
    )


@router.get("/services/upcoming")
async def list_upcoming_services(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
    days_ahead: int = Query(30, ge=1, le=90),
) -> dict:
    from app.application.expenses.list_upcoming_services import ListUpcomingServicesUseCase

    return await ListUpcomingServicesUseCase(db).execute(uuid.UUID(current_user["sub"]), days_ahead=days_ahead)


@router.patch("/services/{service_id}")
async def update_service(
    service_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.update_service import UpdateServiceUseCase

    return await UpdateServiceUseCase(db).execute(
        uuid.UUID(current_user["sub"]), service_id, changes=body
    )


@router.delete("/services/{service_id}")
async def delete_service(
    service_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.delete_service import DeleteServiceUseCase

    return await DeleteServiceUseCase(db).execute(uuid.UUID(current_user["sub"]), service_id)


@router.post("/services/{service_id}/pay", status_code=200)
async def mark_service_paid(
    service_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.mark_service_paid import MarkServicePaidUseCase

    account_id = uuid.UUID(body["account_id"]) if body.get("account_id") else None
    if account_id is None:
        from sqlalchemy import select
        from app.infrastructure.models.financial_account import FinancialAccountModel
        stmt = select(FinancialAccountModel.id).where(
            FinancialAccountModel.user_id == uuid.UUID(current_user["sub"]),
            FinancialAccountModel.status == "active",
        ).limit(1)
        result = await db.execute(stmt)
        row = result.first()
        if row:
            account_id = row[0]
    return await MarkServicePaidUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        service_id,
        amount=float(body.get("paid_amount") or body.get("amount") or 0),
        account_id=account_id or uuid.UUID(current_user["sub"]),
        effective_date=body.get("effective_date") or body.get("payment_date"),
    )


# ======================================================================
# Subscriptions
# ======================================================================


@router.post("/subscriptions", status_code=201)
async def create_subscription(
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from datetime import date as date_type

    from app.application.expenses.create_subscription import CreateSubscriptionUseCase

    start_date = (
        date_type.fromisoformat(body["start_date"])
        if isinstance(body.get("start_date"), str)
        else body.get("start_date")
    )
    return await CreateSubscriptionUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        name=body["name"],
        amount=float(body["amount"]),
        billing_frequency=body.get("billing_frequency", "monthly"),
        category_id=body.get("category_id"),
        start_date=start_date,
        end_date=body.get("end_date"),
        website_url=body.get("website_url"),
    )


@router.get("/subscriptions")
async def list_subscriptions(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
    status: str | None = Query(None),
) -> dict:
    from app.application.expenses.list_subscriptions import ListSubscriptionsUseCase

    return await ListSubscriptionsUseCase(db).execute(uuid.UUID(current_user["sub"]), status=status)


@router.get("/subscriptions/summary")
async def get_subscription_summary(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.analyze_subscriptions import AnalyzeSubscriptionsUseCase

    return await AnalyzeSubscriptionsUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.patch("/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.update_subscription import UpdateSubscriptionUseCase

    return await UpdateSubscriptionUseCase(db).execute(
        uuid.UUID(current_user["sub"]), subscription_id, changes=body
    )


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.delete_subscription import DeleteSubscriptionUseCase

    return await DeleteSubscriptionUseCase(db).execute(
        uuid.UUID(current_user["sub"]), subscription_id
    )


# ======================================================================
# Credit Cards
# ======================================================================


@router.post("/cards", status_code=201)
async def create_credit_card(
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.create_card import CreateCardUseCase

    return await CreateCardUseCase(db).execute(uuid.UUID(current_user["sub"]), **body)


@router.get("/cards")
async def list_credit_cards(
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.list_cards import ListCardsUseCase

    return await ListCardsUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/cards/{card_id}/utilization")
async def get_card_utilization(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db),# noqa: B008
) -> dict:
    from app.application.expenses.get_card_utilization import GetCardUtilizationUseCase

    return await GetCardUtilizationUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)


@router.post("/cards/{card_id}/bills", status_code=201)
async def create_card_bill(
    card_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from datetime import date as date_type

    from app.application.expenses.create_card_bill import CreateCardBillUseCase

    return await CreateCardBillUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        credit_card_id=card_id,
        statement_date=date_type.fromisoformat(body["statement_date"]),
        due_date=date_type.fromisoformat(body["due_date"]),
        total_amount=float(body["total_amount"]),
        minimum_payment=float(body["minimum_payment"]) if body.get("minimum_payment") else None,
        interest_charged=float(body["interest_charged"]) if body.get("interest_charged") else None,
        notes=body.get("notes"),
    )


@router.get("/cards/{card_id}/bills")
async def list_card_bills(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict:
    from app.application.expenses.list_card_bills import ListCardBillsUseCase

    return await ListCardBillsUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)
