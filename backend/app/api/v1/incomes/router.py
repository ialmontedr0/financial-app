"""Income API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db

router = APIRouter(prefix="/incomes", tags=["Incomes"])


# --- Income CRUD ---

@router.post("", status_code=201)
async def create_income(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.create_income import CreateIncomeUseCase

    effective_date = date_type.fromisoformat(body["effective_date"]) if isinstance(body.get("effective_date"), str) else body.get("effective_date")
    tags = body.pop("tags", None)
    return await CreateIncomeUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        account_id=uuid.UUID(body["account_id"]),
        amount=float(body["amount"]),
        currency_code=body.get("currency_code", "DOP"),
        description=body["description"],
        effective_date=effective_date,
        category_id=uuid.UUID(body["category_id"]) if body.get("category_id") else None,
        subcategory_id=uuid.UUID(body["subcategory_id"]) if body.get("subcategory_id") else None,
        status=body.get("status", "completed"),
        notes=body.get("notes"),
        source=body.get("source", "manual"),
        tags=tags,
        income_type=body.get("income_type", "salary"),
        income_status=body.get("income_status", "received"),
        stability=body.get("stability", "fixed"),
        income_source_id=uuid.UUID(body["income_source_id"]) if body.get("income_source_id") else None,
        employer_name=body.get("employer_name"),
        employer_tax_id=body.get("employer_tax_id"),
        gross_amount=float(body["gross_amount"]) if body.get("gross_amount") else None,
        tax_withheld=float(body["tax_withheld"]) if body.get("tax_withheld") else None,
        net_amount=float(body["net_amount"]) if body.get("net_amount") else None,
        frequency=body.get("frequency"),
    )


@router.get("")
async def list_incomes(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    income_type: str | None = Query(None),
    income_status: str | None = Query(None),
    stability: str | None = Query(None),
    income_source_id: str | None = Query(None),
    category_id: str | None = Query(None),
    account_id: str | None = Query(None),
    min_amount: float | None = Query(None),
    max_amount: float | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("effective_date"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.list_incomes import ListIncomesUseCase

    return await ListIncomesUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        income_type=income_type, income_status=income_status, stability=stability,
        income_source_id=uuid.UUID(income_source_id) if income_source_id else None,
        category_id=uuid.UUID(category_id) if category_id else None,
        account_id=uuid.UUID(account_id) if account_id else None,
        min_amount=min_amount, max_amount=max_amount,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        search=search, sort_by=sort_by, sort_order=sort_order,
        page=page, page_size=page_size,
    )


@router.get("/summary")
async def get_income_summary(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    date_from: str = Query(...),
    date_to: str = Query(...),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.get_income_summary import GetIncomeSummaryUseCase

    return await GetIncomeSummaryUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        date_from=date_type.fromisoformat(date_from),
        date_to=date_type.fromisoformat(date_to),
    )


@router.get("/trends")
async def get_income_trends(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    months: int = Query(12, ge=1, le=60),
) -> dict:
    import uuid
    from app.application.incomes.get_income_trends import GetIncomeTrendsUseCase

    return await GetIncomeTrendsUseCase(db).execute(uuid.UUID(current_user["sub"]), months=months)


@router.get("/forecast")
async def get_income_forecast(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.get_income_forecast import GetIncomeForecastUseCase

    return await GetIncomeForecastUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/by-source")
async def get_income_by_source(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    date_from: str = Query(...),
    date_to: str = Query(...),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.get_income_by_source import GetIncomeBySourceUseCase

    return await GetIncomeBySourceUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        date_from=date_type.fromisoformat(date_from),
        date_to=date_type.fromisoformat(date_to),
    )


@router.get("/by-category")
async def get_income_by_category(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    date_from: str = Query(...),
    date_to: str = Query(...),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.get_income_by_category import GetIncomeByCategoryUseCase

    return await GetIncomeByCategoryUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        date_from=date_type.fromisoformat(date_from),
        date_to=date_type.fromisoformat(date_to),
    )


@router.get("/monthly/{year}/{month}")
async def get_monthly_breakdown(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.get_monthly_breakdown import GetMonthlyBreakdownUseCase

    return await GetMonthlyBreakdownUseCase(db).execute(uuid.UUID(current_user["sub"]), year=year, month=month)


@router.get("/recurring-candidates")
async def get_recurring_candidates(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.auto_detect_recurring import AutoDetectRecurringUseCase

    return await AutoDetectRecurringUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.get("/irregular")
async def get_irregular_income(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    months: int = Query(6, ge=1, le=24),
) -> dict:
    import uuid
    from app.application.incomes.detect_irregular import DetectIrregularUseCase

    return await DetectIrregularUseCase(db).execute(uuid.UUID(current_user["sub"]), months=months)


@router.post("/batch-status")
async def batch_update_status(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.batch_update_status import BatchUpdateStatusUseCase

    return await BatchUpdateStatusUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        income_ids=body["income_ids"],
        status=body["status"],
    )


# --- Income Sources ---

@router.post("/sources", status_code=201)
async def create_source(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.create_source import CreateSourceUseCase

    return await CreateSourceUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        name=body["name"],
        income_type=body.get("income_type", "salary"),
        stability=body.get("stability", "fixed"),
        frequency=body.get("frequency"),
        expected_amount=float(body["default_amount"]) if body.get("default_amount") else None,
        default_account_id=uuid.UUID(body["default_account_id"]) if body.get("default_account_id") else None,
        default_category_id=uuid.UUID(body["default_category_id"]) if body.get("default_category_id") else None,
        notes=body.get("description"),
    )


@router.get("/sources")
async def list_sources(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    is_active: bool | None = Query(None),
    income_type: str | None = Query(None),
) -> dict:
    import uuid
    from app.application.incomes.list_sources import ListSourcesUseCase

    return await ListSourcesUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        is_active=is_active,
        income_type=income_type,
    )


@router.post("/sources/{source_id}/create-income", status_code=201)
async def create_from_source(
    source_id: str,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.create_from_source import CreateFromSourceUseCase

    ed = date_type.fromisoformat(body["received_date"]) if body.get("received_date") else date_type.today()
    return await CreateFromSourceUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        uuid.UUID(source_id),
        effective_date=ed,
        amount=float(body["amount"]) if body.get("amount") else None,
        notes=body.get("notes"),
    )


@router.patch("/sources/{source_id}")
async def update_source(
    source_id: str,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.update_source import UpdateSourceUseCase

    return await UpdateSourceUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        uuid.UUID(source_id),
        changes=body,
    )


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.delete_source import DeleteSourceUseCase

    return await DeleteSourceUseCase(db).execute(uuid.UUID(current_user["sub"]), uuid.UUID(source_id))


# --- Income Schedule ---

@router.post("/schedule", status_code=201)
async def create_schedule(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.create_schedule import CreateScheduleUseCase

    return await CreateScheduleUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        description=body["description"],
        amount=float(body["amount"]),
        account_id=uuid.UUID(body["account_id"]),
        expected_date=date_type.fromisoformat(body["expected_date"]),
        income_source_id=uuid.UUID(body["income_source_id"]) if body.get("income_source_id") else None,
        currency_code=body.get("currency_code", "DOP"),
        frequency=body.get("frequency"),
        projection_method=body.get("projection_method"),
        notes=body.get("notes"),
    )


@router.get("/schedule")
async def list_schedule(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.list_schedule import ListScheduleUseCase

    return await ListScheduleUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        status=status,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
    )


@router.get("/schedule/projected")
async def get_projected_income(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    months: int = Query(6, ge=1, le=24),
) -> dict:
    import uuid
    from app.infrastructure.repositories.income_repository import IncomeRepository

    return await IncomeRepository(db).get_projected_income(uuid.UUID(current_user["sub"]), months=months)


@router.post("/schedule/{schedule_id}/receive", status_code=201)
async def receive_scheduled(
    schedule_id: str,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from datetime import date as date_type
    from app.application.incomes.receive_scheduled import ReceiveScheduledUseCase

    ed = date_type.fromisoformat(body["received_date"]) if body.get("received_date") else None
    return await ReceiveScheduledUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        uuid.UUID(schedule_id),
        effective_date=ed,
        amount=float(body["amount"]) if body.get("amount") else None,
        notes=body.get("notes"),
        tags=body.get("tags"),
    )


@router.patch("/schedule/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.update_schedule import UpdateScheduleUseCase

    return await UpdateScheduleUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        uuid.UUID(schedule_id),
        changes=body,
    )


@router.delete("/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.delete_schedule import DeleteScheduleUseCase

    return await DeleteScheduleUseCase(db).execute(uuid.UUID(current_user["sub"]), uuid.UUID(schedule_id))


# --- Recurring ---

@router.get("/recurring")
async def list_recurring_incomes(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.list_recurring_incomes import ListRecurringIncomesUseCase

    return await ListRecurringIncomesUseCase(db).execute(uuid.UUID(current_user["sub"]))


@router.post("/recurring/process")
async def process_recurring_incomes(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.application.incomes.process_recurring_income import ProcessRecurringIncomeUseCase

    return await ProcessRecurringIncomeUseCase(db).execute()


# --- Income Detail (MUST be after all static routes) ---

@router.get("/{income_id}")
async def get_income(
    income_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.get_income import GetIncomeUseCase

    return await GetIncomeUseCase(db).execute(uuid.UUID(current_user["sub"]), uuid.UUID(income_id))


@router.patch("/{income_id}")
async def update_income(
    income_id: str,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.update_income import UpdateIncomeUseCase

    return await UpdateIncomeUseCase(db).execute(
        uuid.UUID(current_user["sub"]),
        uuid.UUID(income_id),
        changes=body,
    )


@router.delete("/{income_id}")
async def delete_income(
    income_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    import uuid
    from app.application.incomes.delete_income import DeleteIncomeUseCase

    return await DeleteIncomeUseCase(db).execute(uuid.UUID(current_user["sub"]), uuid.UUID(income_id))
