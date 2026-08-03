"""Tax endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_user, get_db
from app.application.taxes.create_category import CreateTaxCategoryUseCase
from app.application.taxes.create_deduction import CreateTaxDeductionUseCase
from app.application.taxes.delete_category import DeleteTaxCategoryUseCase
from app.application.taxes.delete_deduction import DeleteTaxDeductionUseCase
from app.application.taxes.get_deduction import GetTaxDeductionUseCase
from app.application.taxes.get_tax_summary import GetTaxSummaryUseCase
from app.application.taxes.list_categories import ListTaxCategoriesUseCase
from app.application.taxes.list_deductions import ListTaxDeductionsUseCase
from app.application.taxes.update_deduction import UpdateTaxDeductionUseCase

router = APIRouter(prefix="/taxes", tags=["Taxes"])


@router.post("/categories", status_code=201)
async def create_category(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await CreateTaxCategoryUseCase(session).execute(
        user_id=user_id,
        name=body.get("name", ""),
        tax_year=body.get("tax_year"),
        description=body.get("description"),
    )


@router.get("/categories")
async def list_categories(
    tax_year: int | None = None,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListTaxCategoriesUseCase(session).execute(user_id, tax_year=tax_year)


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeleteTaxCategoryUseCase(session).execute(user_id, category_id)


@router.post("/deductions", status_code=201)
async def create_deduction(
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    from datetime import date

    user_id = uuid.UUID(current_user["sub"])
    return await CreateTaxDeductionUseCase(session).execute(
        user_id=user_id,
        description=body.get("description", ""),
        amount=body.get("amount", 0),
        date_value=date.fromisoformat(body["date"]),
        tax_year=body.get("tax_year"),
        category_id=uuid.UUID(body["category_id"]) if body.get("category_id") else None,
        deductible=body.get("deductible"),
        receipt_url=body.get("receipt_url"),
    )


@router.get("/deductions")
async def list_deductions(
    tax_year: int | None = None,
    category_id: uuid.UUID | None = None,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await ListTaxDeductionsUseCase(session).execute(
        user_id, tax_year=tax_year, category_id=category_id
    )


@router.get("/deductions/{deduction_id}")
async def get_deduction(
    deduction_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetTaxDeductionUseCase(session).execute(user_id, deduction_id)


@router.patch("/deductions/{deduction_id}")
async def update_deduction(
    deduction_id: uuid.UUID,
    body: dict,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await UpdateTaxDeductionUseCase(session).execute(user_id, deduction_id, body)


@router.delete("/deductions/{deduction_id}")
async def delete_deduction(
    deduction_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await DeleteTaxDeductionUseCase(session).execute(user_id, deduction_id)


@router.get("/summary/{year}")
async def get_tax_summary(
    year: int,
    current_user: dict = Depends(get_current_active_user),
    session=Depends(get_db),
):
    user_id = uuid.UUID(current_user["sub"])
    return await GetTaxSummaryUseCase(session).execute(user_id, year)
