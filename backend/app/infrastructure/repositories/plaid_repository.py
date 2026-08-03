"""Plaid repository — database operations for linked Plaid items."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.plaid_item import PlaidItemModel

logger = structlog.get_logger()


class PlaidRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_item(self, user_id: uuid.UUID, **kwargs: object) -> PlaidItemModel:
        item = PlaidItemModel(user_id=user_id, **kwargs)
        self._session.add(item)
        await self._session.flush()
        logger.info("plaid_item_created", item_id=str(item.id), user_id=str(user_id))
        return item

    async def get_item(self, item_id: uuid.UUID, user_id: uuid.UUID) -> PlaidItemModel | None:
        stmt = select(PlaidItemModel).where(
            PlaidItemModel.id == item_id,
            PlaidItemModel.user_id == user_id,
            PlaidItemModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_item_by_plaid_id(self, plaid_item_id: str) -> PlaidItemModel | None:
        stmt = select(PlaidItemModel).where(
            PlaidItemModel.item_id == plaid_item_id,
            PlaidItemModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_items(self, user_id: uuid.UUID) -> list[PlaidItemModel]:
        stmt = (
            select(PlaidItemModel)
            .where(
                PlaidItemModel.user_id == user_id,
                PlaidItemModel.deleted_at.is_(None),
            )
            .order_by(PlaidItemModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_item(
        self, item: PlaidItemModel, **kwargs: object
    ) -> PlaidItemModel:
        for key, value in kwargs.items():
            if value is not None or key in {"status"}:
                setattr(item, key, value)
        await self._session.flush()
        return item

    async def delete_item(self, item: PlaidItemModel) -> None:
        item.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def touch_sync(self, item: PlaidItemModel) -> None:
        item.last_sync_at = datetime.now(UTC)
        await self._session.flush()
