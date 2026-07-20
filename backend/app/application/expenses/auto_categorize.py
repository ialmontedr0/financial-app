"""Use case: Auto-categorize uncategorized expenses using CategoryRuleModel."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import and_, select  # noqa: F401

from app.infrastructure.models.category_rule import CategoryRuleModel
from app.infrastructure.models.transaction import TransactionModel
from app.infrastructure.repositories.transaction_repository import TransactionRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class AutoCategorizeUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TransactionRepository(session)

    async def execute(self, user_id: uuid.UUID, *, limit: int = 100) -> dict:
        # Get uncategorized expenses
        stmt = (
            select(TransactionModel)
            .where(
                TransactionModel.user_id == user_id,
                TransactionModel.deleted_at.is_(None),
                TransactionModel.transaction_type == "expense",
                TransactionModel.category_id.is_(None),
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        uncategorized = list(result.scalars().all())

        if not uncategorized:
            return {"categorized": 0, "remaining": 0, "details": []}

        # Get all rules for this user
        rules_stmt = select(CategoryRuleModel).where(
            CategoryRuleModel.user_id == user_id,
            CategoryRuleModel.is_active.is_(True),
        )
        rules_result = await self._session.execute(rules_stmt)
        rules = list(rules_result.scalars().all())

        categorized_count = 0
        details: list[dict] = []

        for tx in uncategorized:
            matched_category_id = None
            matched_subcategory_id = None
            matched_rule_id = None

            for rule in rules:
                is_match = False
                if rule.keyword:
                    keywords = [k.strip().lower() for k in rule.keyword.split("|")]
                    desc_lower = (tx.description or "").lower()
                    if any(kw in desc_lower for kw in keywords):
                        is_match = True

                if is_match:
                    matched_category_id = rule.target_category_id
                    matched_subcategory_id = rule.target_subcategory_id
                    matched_rule_id = rule.id
                    break

            if matched_category_id:
                await self._repo.update(
                    tx.id,
                    user_id,
                    category_id=matched_category_id,
                    subcategory_id=matched_subcategory_id,
                )
                categorized_count += 1
                details.append(
                    {
                        "transaction_id": str(tx.id),
                        "description": tx.description,
                        "category_id": str(matched_category_id),
                        "subcategory_id": str(matched_subcategory_id)
                        if matched_subcategory_id
                        else None,
                        "rule_id": str(matched_rule_id),
                    }
                )
                logger.info("auto_categorized", tx_id=str(tx.id), category=str(matched_category_id))

        return {
            "categorized": categorized_count,
            "remaining": len(uncategorized) - categorized_count,
            "total_rules_evaluated": len(rules),
            "details": details,
        }
