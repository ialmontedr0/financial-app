"""Categories API router - Transaction classification."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_active_user, get_db
from app.api.v1.categories.schemas import (
    CategorizeRequest,
    CategorizeResponse,
    CategoryDetailResponse,
    CategoryResponse,
    CategoryStatsResponse,
    CreateCategoryRequest,
    CreateSubcategoryRequest,
    DeleteCategoryResponse,
    ListCategoriesResponse,
    SubcategoryResponse,
    UpdateCategoryRequest,
    UpdateSubcategoryRequest,
)
from app.application.categories.categorize_transaction import CategorizeTransactionUseCase
from app.application.categories.create_category import CreateCategoryUseCase
from app.application.categories.create_subcategory import CreateSubcategoryUseCase
from app.application.categories.delete_category import DeleteCategoryUseCase
from app.application.categories.delete_subcategory import DeleteSubcategoryUseCase
from app.application.categories.get_category import GetCategoryUseCase
from app.application.categories.get_category_stats import GetCategoryStatsUseCase
from app.application.categories.list_categories import ListCategoriesUseCase
from app.application.categories.update_category import UpdateCategoryUseCase
from app.application.categories.update_subcategory import UpdateSubcategoryUseCase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/categories", tags=["Categories"])


# ============================================================
# List Categories
# ============================================================
@router.get(
    "",
    response_model=ListCategoriesResponse,
    summary="List categories",
    description="List all visible categories (system + user's own) with subcategories.",
)
async def list_categories(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    category_type: str | None = Query(None, description="Filter: expense, income, transfer, adjustment"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
) -> dict:
    """List all categories."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = ListCategoriesUseCase(db)
    categories = await use_case.execute(
        user_id, category_type=category_type, include_inactive=include_inactive
    )
    return {"categories": categories, "total": len(categories)}


# ============================================================
# Create Category
# ============================================================
@router.post(
    "",
    response_model=CategoryDetailResponse,
    status_code=201,
    summary="Create a new category",
    description="Create a custom category for the user.",
)
async def create_category(
    body: CreateCategoryRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new category."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True)
    use_case = CreateCategoryUseCase(db)
    return await use_case.execute(user_id, **fields)


# ============================================================
# Get Category Detail
# ============================================================
@router.get(
    "/{category_id}",
    response_model=CategoryDetailResponse,
    summary="Get category details",
    description="Get full category details including subcategories.",
)
async def get_category(
    category_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single category with subcategories."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetCategoryUseCase(db)
    return await use_case.execute(user_id, category_id)


# ============================================================
# Update Category
# ============================================================
@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category",
    description="Partial update of category fields. System categories have limited edit.",
)
async def update_category(
    category_id: uuid.UUID,
    body: UpdateCategoryRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a category (partial)."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    use_case = UpdateCategoryUseCase(db)
    return await use_case.execute(user_id, category_id, **fields)


# ============================================================
# Delete Category
# ============================================================
@router.delete(
    "/{category_id}",
    response_model=DeleteCategoryResponse,
    summary="Delete category",
    description="Soft-delete a user category. System categories cannot be deleted.",
)
async def delete_category(
    category_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a category."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = DeleteCategoryUseCase(db)
    return await use_case.execute(user_id, category_id)


# ============================================================
# Create Subcategory
# ============================================================
@router.post(
    "/{category_id}/subcategories",
    response_model=SubcategoryResponse,
    status_code=201,
    summary="Create subcategory",
    description="Create a subcategory under an existing category.",
)
async def create_subcategory(
    category_id: uuid.UUID,
    body: CreateSubcategoryRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a subcategory."""
    user_id = uuid.UUID(current_user["sub"])
    fields = body.model_dump(exclude_unset=True)
    use_case = CreateSubcategoryUseCase(db)
    return await use_case.execute(user_id, category_id, **fields)


# ============================================================
# Update Subcategory
# ============================================================
@router.patch(
    "/subcategories/{subcategory_id}",
    response_model=SubcategoryResponse,
    summary="Update subcategory",
    description="Partial update of subcategory fields.",
)
async def update_subcategory(
    subcategory_id: uuid.UUID,
    body: UpdateSubcategoryRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a subcategory (partial)."""
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    use_case = UpdateSubcategoryUseCase(db)
    return await use_case.execute(subcategory_id, **fields)


# ============================================================
# Delete Subcategory
# ============================================================
@router.delete(
    "/subcategories/{subcategory_id}",
    summary="Delete subcategory",
    description="Soft-delete a subcategory.",
)
async def delete_subcategory(
    subcategory_id: uuid.UUID,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a subcategory."""
    use_case = DeleteSubcategoryUseCase(db)
    return await use_case.execute(subcategory_id)


# ============================================================
# Categorize Transaction
# ============================================================
@router.post(
    "/categorize",
    response_model=CategorizeResponse,
    summary="Categorize a transaction",
    description="Auto-categorize a transaction using rules + ML classifier.",
)
async def categorize_transaction(
    body: CategorizeRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Categorize a transaction."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = CategorizeTransactionUseCase(db)
    return await use_case.execute(
        user_id,
        description=body.description,
        amount=Decimal(str(body.amount)) if body.amount is not None else None,
        merchant_name=body.merchant_name,
    )


# ============================================================
# Category Stats
# ============================================================
@router.get(
    "/stats/overview",
    response_model=CategoryStatsResponse,
    summary="Get category statistics",
    description="Get category usage statistics overview.",
)
async def get_category_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get category stats."""
    user_id = uuid.UUID(current_user["sub"])
    use_case = GetCategoryStatsUseCase(db)
    return await use_case.execute(user_id)
