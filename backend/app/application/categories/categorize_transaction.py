"""Use case: Categorize a transaction using rules + AI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.infrastructure.repositories.category_repository import CategoryRepository

if TYPE_CHECKING:
    import uuid
    from decimal import Decimal

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.infrastructure.models.category import CategoryModel

logger = structlog.get_logger()


class CategorizeTransactionUseCase:
    """Categorize a transaction using rule engine + ML classifier."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CategoryRepository(session)

    async def execute(
        self,
        user_id: uuid.UUID,
        description: str,
        amount: Decimal | None = None,
        merchant_name: str | None = None,
    ) -> dict:
        """
        Categorize a transaction.

        Priority:
        1. User rules (exact match)
        2. System rules (exact match)
        3. ML classifier (if confidence > 0.7)
        4. Uncategorised fallback
        """
        search_text = merchant_name or description

        # Step 1: Try rule-based matching
        matching_rules = await self._repo.find_matching_rules(
            text=search_text,
            amount=amount,
            user_id=user_id,
        )

        if matching_rules:
            best_rule = matching_rules[0]  # Already sorted by priority
            await self._repo.increment_rule_hit(best_rule.id)

            result = {
                "category_id": str(best_rule.target_category_id),
                "subcategory_id": str(best_rule.target_subcategory_id) if best_rule.target_subcategory_id else None,
                "method": "rule",
                "confidence": 1.0,
                "rule_id": str(best_rule.id),
                "rule_name": best_rule.rule_name,
            }
            logger.info(
                "transaction_categorized_by_rule",
                user_id=str(user_id),
                rule_id=str(best_rule.id),
                category_id=str(best_rule.target_category_id),
            )
            return result

        # Step 2: Try ML classifier
        ml_result = await self._classify_with_ml(search_text, user_id)
        if ml_result and ml_result["confidence"] > 0.7:
            logger.info(
                "transaction_categorized_by_ml",
                user_id=str(user_id),
                category_id=ml_result["category_id"],
                confidence=ml_result["confidence"],
            )
            return ml_result

        # Step 3: Fallback to "Sin Categoria"
        sin_cat = await self._find_sin_categoria()
        return {
            "category_id": str(sin_cat.id) if sin_cat else None,
            "subcategory_id": None,
            "method": "fallback",
            "confidence": 0.0,
            "rule_id": None,
            "rule_name": None,
        }

    async def _classify_with_ml(self, text: str, user_id: uuid.UUID) -> dict | None:
        """Use the ML classifier to predict a category."""
        from app.ai.classifiers.ml_classifier import classifier
        from sqlalchemy import select

        from app.infrastructure.models.category import CategoryModel

        if not classifier.is_trained:
            classifier.load_model(str(user_id))

        if not classifier.is_trained:
            return None

        result = await classifier.predict(text)
        if result is None:
            return None

        confidence = result["confidence"]
        category_name = result["category_slug"]

        # Look up the category by name
        stmt = select(CategoryModel).where(
            CategoryModel.name == category_name,
            CategoryModel.deleted_at.is_(None),
            (CategoryModel.is_system.is_(True)) | (CategoryModel.user_id == user_id),
        )
        db_result = await self._session.execute(stmt)
        cat = db_result.scalar_one_or_none()

        if cat is None:
            return None

        return {
            "category_id": str(cat.id),
            "subcategory_id": None,
            "method": "ml",
            "confidence": round(confidence, 4),
            "rule_id": None,
            "rule_name": None,
        }

    async def _find_sin_categoria(self) -> CategoryModel | None:
        """Find the 'Sin Categoria' system category."""
        from sqlalchemy import select

        from app.infrastructure.models.category import CategoryModel

        stmt = select(CategoryModel).where(
            CategoryModel.name == "Sin Categoria",
            CategoryModel.is_system.is_(True),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
