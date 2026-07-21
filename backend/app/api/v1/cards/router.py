"""Credit card management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/cards", tags=["Credit Cards"])


# ======================================================================
# Card CRUD
# ======================================================================


@router.get("", status_code=200)
async def list_cards(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.expenses.list_cards import ListCardsUseCase

    return await ListCardsUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/summary")
async def get_cards_summary(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.get_cards_summary import GetCardsSummaryUseCase

    return await GetCardsSummaryUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/{card_id}")
async def get_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.get_card import GetCardUseCase

    return await GetCardUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)


@router.post("", status_code=201)
async def create_card(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.expenses.create_card import CreateCardUseCase

    return await CreateCardUseCase(db).execute(uuid.UUID(current_user["sub"]), **body)


@router.patch("/{card_id}")
async def update_card(
    card_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.update_card import UpdateCardUseCase

    return await UpdateCardUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id, changes=body)


@router.delete("/{card_id}")
async def delete_card(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.delete_card import DeleteCardUseCase

    return await DeleteCardUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)


# ======================================================================
# Utilization
# ======================================================================


@router.get("/{card_id}/utilization")
async def get_card_utilization(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.infrastructure.repositories.card_repository import CardRepository

    repo = CardRepository(db)
    util = await repo.calculate_utilization(card_id, uuid.UUID(current_user["sub"]))
    if util is None:
        from app.middleware.error_handler import NotFoundError
        raise NotFoundError("CreditCard")
    return util


@router.get("/{card_id}/utilization/history")
async def get_utilization_history(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    months: int = Query(6, ge=1, le=24),
) -> dict:
    from app.application.cards.get_utilization_history import GetUtilizationHistoryUseCase

    return await GetUtilizationHistoryUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id, months)


@router.get("/{card_id}/spending")
async def get_spending_by_category(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    period_start: str | None = Query(None),
    period_end: str | None = Query(None),
) -> dict:
    from datetime import date as date_type

    from app.application.cards.get_spending_by_category import GetSpendingByCategoryUseCase

    start = date_type.fromisoformat(period_start) if period_start else None
    end = date_type.fromisoformat(period_end) if period_end else None
    return await GetSpendingByCategoryUseCase(db).execute(
        uuid.UUID(current_user["sub"]), card_id, start, end
    )


# ======================================================================
# Bills
# ======================================================================


@router.post("/{card_id}/bills", status_code=201)
async def create_card_bill(
    card_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
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


@router.get("/{card_id}/bills")
async def list_card_bills(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.expenses.list_card_bills import ListCardBillsUseCase

    return await ListCardBillsUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)


@router.patch("/{card_id}/bills/{bill_id}")
async def update_card_bill(
    card_id: uuid.UUID,
    bill_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.update_card_bill import UpdateCardBillUseCase

    return await UpdateCardBillUseCase(db).execute(
        uuid.UUID(current_user["sub"]), card_id, bill_id, changes=body
    )


@router.delete("/{card_id}/bills/{bill_id}")
async def delete_card_bill(
    card_id: uuid.UUID,
    bill_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.delete_card_bill import DeleteCardBillUseCase

    return await DeleteCardBillUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id, bill_id)


@router.post("/{card_id}/bills/{bill_id}/pay", status_code=200)
async def pay_card_bill(
    card_id: uuid.UUID,
    bill_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.pay_card_bill import PayCardBillUseCase

    return await PayCardBillUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        card_id,
        bill_id,
        amount=float(body["amount"]),
        payment_method=body.get("payment_method", "manual"),
    )


@router.post("/{card_id}/statements/generate", status_code=200)
async def generate_statement(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.generate_statement import GenerateStatementUseCase

    return await GenerateStatementUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)


# ======================================================================
# Spending Limits
# ======================================================================


@router.get("/{card_id}/limits")
async def list_spending_limits(
    card_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.list_spending_limits import ListSpendingLimitsUseCase

    return await ListSpendingLimitsUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id)


@router.post("/{card_id}/limits", status_code=201)
async def create_spending_limit(
    card_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.create_spending_limit import CreateSpendingLimitUseCase

    return await CreateSpendingLimitUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        card_id,
        limit_type=body["limit_type"],
        limit_amount=float(body["limit_amount"]),
        category_id=uuid.UUID(body["category_id"]) if body.get("category_id") else None,
        alert_threshold=body.get("alert_threshold", 80),
        alert_enabled=body.get("alert_enabled", True),
        description=body.get("description"),
    )


@router.patch("/{card_id}/limits/{limit_id}")
async def update_spending_limit(
    card_id: uuid.UUID,
    limit_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.update_spending_limit import UpdateSpendingLimitUseCase

    return await UpdateSpendingLimitUseCase(db).execute(
        uuid.UUID(current_user["sub"]), card_id, limit_id, changes=body
    )


@router.delete("/{card_id}/limits/{limit_id}")
async def delete_spending_limit(
    card_id: uuid.UUID,
    limit_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.delete_spending_limit import DeleteSpendingLimitUseCase

    return await DeleteSpendingLimitUseCase(db).execute(uuid.UUID(current_user["sub"]), card_id, limit_id)


# ======================================================================
# Card Alerts
# ======================================================================


@router.get("/alerts/all")
async def list_card_alerts(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    credit_card_id: str | None = Query(None),
    is_read: bool | None = Query(None),
    alert_type: str | None = Query(None),
    severity: str | None = Query(None),
) -> dict:
    from app.application.cards.list_card_alerts import ListCardAlertsUseCase

    return await ListCardAlertsUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        credit_card_id=uuid.UUID(credit_card_id) if credit_card_id else None,
        is_read=is_read,
        alert_type=alert_type,
        severity=severity,
    )


@router.post("/alerts/read", status_code=200)
async def mark_card_alert_read(
    body: dict,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.mark_card_alert_read import MarkCardAlertReadUseCase

    return await MarkCardAlertReadUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        alert_id=uuid.UUID(body["alert_id"]) if body.get("alert_id") else None,
        mark_all=body.get("mark_all", False),
    )


@router.post("/alerts/{alert_id}/dismiss", status_code=200)
async def dismiss_card_alert(
    alert_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.dismiss_card_alert import DismissCardAlertUseCase

    return await DismissCardAlertUseCase(db).execute(uuid.UUID(current_user["sub"]), alert_id)


@router.post("/alerts/check", status_code=200)
async def check_card_alerts(
    current_user: dict = Depends(get_current_active_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict:
    from app.application.cards.check_card_alerts import CheckCardAlertsUseCase

    return await CheckCardAlertsUseCase(db).execute(uuid.UUID(current_user["sub"]))
