"""Pydantic schemas for Categories API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================
# Subcategory (must be defined before CategoryDetailResponse)
# ============================================================
class SubcategoryListItem(BaseModel):
    """Subcategory within a category list."""

    id: str
    name: str
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0


class SubcategoryDetail(BaseModel):
    """Subcategory with full detail."""

    id: str
    name: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    keywords: str | None = None


class SubcategoryResponse(BaseModel):
    """Subcategory response for create/update."""

    id: str
    name: str
    description: str | None = None
    category_id: str
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


# ============================================================
# Create Category
# ============================================================
class CreateCategoryRequest(BaseModel):
    """Request to create a new category."""

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str | None = Field(None, max_length=500)
    category_type: str = Field(
        default="expense", description="expense, income, transfer, adjustment"
    )
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=7, description="Hex color #RRGGBB")
    sort_order: int = Field(default=0)
    keywords: str | None = Field(None, description="Comma-separated keywords")


class CategoryResponse(BaseModel):
    """Category response."""

    id: str
    name: str
    description: str | None = None
    category_type: str
    is_system: bool = False
    is_active: bool = True
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class CategoryDetailResponse(BaseModel):
    """Category with subcategories."""

    id: str
    name: str
    description: str | None = None
    category_type: str
    is_system: bool = False
    is_active: bool = True
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    keywords: str | None = None
    subcategories: list[SubcategoryDetail] = []
    created_at: str | None = None
    updated_at: str | None = None


# ============================================================
# Update Category
# ============================================================
class UpdateCategoryRequest(BaseModel):
    """Request to update a category (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    category_type: str | None = None
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=7)
    sort_order: int | None = None
    keywords: str | None = None
    is_active: bool | None = None


# ============================================================
# Delete Category
# ============================================================
class DeleteCategoryResponse(BaseModel):
    """Category deletion response."""

    message: str
    category_id: str


# ============================================================
# List Categories
# ============================================================
class CategoryListItem(BaseModel):
    """Category list item with subcategories."""

    id: str
    name: str
    description: str | None = None
    category_type: str
    is_system: bool
    is_active: bool
    icon: str | None = None
    color: str | None = None
    sort_order: int = 0
    subcategories: list[SubcategoryListItem] = []
    created_at: str | None = None


class ListCategoriesResponse(BaseModel):
    """List of categories."""

    categories: list[CategoryListItem]
    total: int


# ============================================================
# Subcategory CRUD
# ============================================================
class CreateSubcategoryRequest(BaseModel):
    """Request to create a subcategory."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=7)
    sort_order: int = Field(default=0)
    keywords: str | None = None


class UpdateSubcategoryRequest(BaseModel):
    """Request to update a subcategory."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    icon: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=7)
    sort_order: int | None = None
    keywords: str | None = None
    is_active: bool | None = None


# ============================================================
# Categorize Transaction
# ============================================================
class CategorizeRequest(BaseModel):
    """Request to categorize a transaction."""

    description: str = Field(..., min_length=1, max_length=500)
    amount: float | None = Field(None, description="Transaction amount")
    merchant_name: str | None = Field(None, max_length=200)


class CategorizeResponse(BaseModel):
    """Categorization result."""

    category_id: str | None = None
    subcategory_id: str | None = None
    method: str  # rule, ml, fallback
    confidence: float
    rule_id: str | None = None
    rule_name: str | None = None


# ============================================================
# Stats
# ============================================================
class CategoryStatsResponse(BaseModel):
    """Category usage statistics."""

    total_categories: int
    system_categories: int
    user_categories: int
    by_type: dict[str, int]
