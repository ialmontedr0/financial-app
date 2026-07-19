"""Repository for category persistence."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select, update

from app.infrastructure.models.category import CategoryModel
from app.infrastructure.models.category_rule import CategoryRuleModel
from app.infrastructure.models.subcategory import SubcategoryModel

if TYPE_CHECKING:
    import uuid
    from decimal import Decimal

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class CategoryRepository:
    """Repository for CategoryModel, SubcategoryModel, CategoryRuleModel operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ======================================================================
    # Categories
    # ======================================================================

    async def create_category(
        self,
        user_id: uuid.UUID | None,
        **kwargs: str | int | bool | None,
    ) -> CategoryModel:
        """Create a new category."""
        cat = CategoryModel(user_id=user_id, **kwargs)
        self._session.add(cat)
        await self._session.flush()
        logger.info(
            "category_created",
            user_id=str(user_id),
            category_id=str(cat.id),
            name=cat.name,
            is_system=cat.is_system,
        )
        return cat

    async def get_category_by_id(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> CategoryModel | None:
        """Get category by ID. System categories visible to all; user categories scoped."""
        stmt = select(CategoryModel).where(
            CategoryModel.id == category_id,
            CategoryModel.deleted_at.is_(None),
        )
        if user_id is not None:
            # System categories OR user's own categories
            stmt = stmt.where(
                (CategoryModel.is_system.is_(True)) | (CategoryModel.user_id == user_id)
            )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_categories(
        self,
        user_id: uuid.UUID | None = None,
        *,
        category_type: str | None = None,
        include_system: bool = True,
        include_inactive: bool = False,
    ) -> list[CategoryModel]:
        """List categories: system + user's own."""
        stmt = select(CategoryModel).where(
            CategoryModel.deleted_at.is_(None),
        )

        if include_system and user_id is not None:
            stmt = stmt.where(
                (CategoryModel.is_system.is_(True)) | (CategoryModel.user_id == user_id)
            )
        elif user_id is not None:
            stmt = stmt.where(CategoryModel.user_id == user_id)

        if category_type:
            stmt = stmt.where(CategoryModel.category_type == category_type)

        if not include_inactive:
            stmt = stmt.where(CategoryModel.is_active.is_(True))

        stmt = stmt.order_by(
            CategoryModel.sort_order.asc(),
            CategoryModel.name.asc(),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        **kwargs: str | int | bool | None,
    ) -> CategoryModel | None:
        """Update category fields. Returns None if not found."""
        cat = await self.get_category_by_id(category_id, user_id)
        if cat is None:
            return None

        # System categories: only allow certain fields
        if cat.is_system:
            allowed_for_system = {"icon", "color", "sort_order", "keywords"}
            invalid = set(kwargs.keys()) - allowed_for_system
            if invalid:
                raise ValueError(
                    f"Categorias del sistema no permiten modificar: {', '.join(invalid)}"
                )

        for key, value in kwargs.items():
            if hasattr(cat, key):
                setattr(cat, key, value)
        await self._session.flush()
        await self._session.refresh(cat)
        logger.info(
            "category_updated",
            user_id=str(user_id),
            category_id=str(category_id),
            fields=list(kwargs.keys()),
        )
        return cat

    async def delete_category(
        self,
        category_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> bool:
        """Soft-delete a category. System categories cannot be deleted."""
        cat = await self.get_category_by_id(category_id, user_id)
        if cat is None or cat.is_system:
            return False
        from datetime import UTC, datetime

        cat.deleted_at = datetime.now(UTC)
        cat.is_active = False
        await self._session.flush()
        logger.info("category_deleted", category_id=str(category_id))
        return True

    # ======================================================================
    # Subcategories
    # ======================================================================

    async def create_subcategory(
        self,
        category_id: uuid.UUID,
        **kwargs: str | int | bool | None,
    ) -> SubcategoryModel:
        """Create a subcategory."""
        sub = SubcategoryModel(category_id=category_id, **kwargs)
        self._session.add(sub)
        await self._session.flush()
        logger.info(
            "subcategory_created",
            category_id=str(category_id),
            subcategory_id=str(sub.id),
            name=sub.name,
        )
        return sub

    async def get_subcategory_by_id(
        self,
        subcategory_id: uuid.UUID,
    ) -> SubcategoryModel | None:
        """Get subcategory by ID."""
        stmt = select(SubcategoryModel).where(
            SubcategoryModel.id == subcategory_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_subcategories(
        self,
        category_id: uuid.UUID,
    ) -> list[SubcategoryModel]:
        """List subcategories for a category."""
        stmt = (
            select(SubcategoryModel)
            .where(
                SubcategoryModel.category_id == category_id,
                SubcategoryModel.is_active.is_(True),
            )
            .order_by(SubcategoryModel.sort_order.asc(), SubcategoryModel.name.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_subcategory(
        self,
        subcategory_id: uuid.UUID,
        **kwargs: str | int | bool | None,
    ) -> SubcategoryModel | None:
        """Update subcategory fields."""
        sub = await self.get_subcategory_by_id(subcategory_id)
        if sub is None:
            return None
        for key, value in kwargs.items():
            if hasattr(sub, key):
                setattr(sub, key, value)
        await self._session.flush()
        await self._session.refresh(sub)
        return sub

    async def delete_subcategory(
        self,
        subcategory_id: uuid.UUID,
    ) -> bool:
        """Soft-delete a subcategory (set is_active=False)."""
        sub = await self.get_subcategory_by_id(subcategory_id)
        if sub is None:
            return False
        sub.is_active = False
        await self._session.flush()
        return True

    # ======================================================================
    # Rules
    # ======================================================================

    async def create_rule(
        self,
        user_id: uuid.UUID | None,
        **kwargs: str | int | bool | uuid.UUID | None,
    ) -> CategoryRuleModel:
        """Create a category rule."""
        rule = CategoryRuleModel(user_id=user_id, **kwargs)
        self._session.add(rule)
        await self._session.flush()
        logger.info(
            "category_rule_created",
            rule_id=str(rule.id),
            rule_name=rule.rule_name,
        )
        return rule

    async def list_rules(
        self,
        user_id: uuid.UUID | None = None,
        *,
        active_only: bool = True,
    ) -> list[CategoryRuleModel]:
        """List rules: system + user's own, ordered by priority."""
        stmt = select(CategoryRuleModel)
        if user_id is not None:
            stmt = stmt.where(
                (CategoryRuleModel.is_system.is_(True))
                | (CategoryRuleModel.user_id == user_id)
            )
        if active_only:
            stmt = stmt.where(CategoryRuleModel.is_active.is_(True))
        stmt = stmt.order_by(CategoryRuleModel.priority.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def increment_rule_hit(self, rule_id: uuid.UUID) -> None:
        """Increment the hit count for a rule."""
        stmt = (
            update(CategoryRuleModel)
            .where(CategoryRuleModel.id == rule_id)
            .values(hit_count=CategoryRuleModel.hit_count + 1)
        )
        await self._session.execute(stmt)

    # ======================================================================
    # Categorization
    # ======================================================================

    async def find_matching_rules(
        self,
        text: str,
        amount: Decimal | None = None,
        user_id: uuid.UUID | None = None,
    ) -> list[CategoryRuleModel]:
        """Find rules that match the given text/amount. Returns sorted by priority."""
        rules = await self.list_rules(user_id, active_only=True)
        matches: list[CategoryRuleModel] = []

        text_lower = text.lower().strip()

        for rule in rules:
            matched = False

            if rule.pattern_type == "keyword":
                keywords = [k.strip().lower() for k in rule.pattern.split("|")]
                matched = any(kw in text_lower for kw in keywords)

            elif rule.pattern_type == "regex":
                try:
                    matched = bool(re.search(rule.pattern, text, re.IGNORECASE))
                except re.error:
                    continue

            elif rule.pattern_type == "merchant_exact":
                matched = rule.pattern.lower().strip() == text_lower

            elif rule.pattern_type == "amount_range" and amount is not None:
                min_ok = rule.amount_min is None or amount >= rule.amount_min
                max_ok = rule.amount_max is None or amount <= rule.amount_max
                matched = min_ok and max_ok

            if matched:
                matches.append(rule)

        return matches
