"""Repository for durable idempotency keys."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.infrastructure.models.idempotency_key import IdempotencyKeyModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> IdempotencyKeyModel | None:
        stmt = select(IdempotencyKeyModel).where(IdempotencyKeyModel.key == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self, *, key: str, method: str, path: str, user_id=None, expires_at=None
    ) -> IdempotencyKeyModel:
        record = IdempotencyKeyModel(
            key=key, method=method, path=path, user_id=user_id, expires_at=expires_at
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def complete(self, key: str, *, status_code: int, response_body: str) -> None:
        record = await self.get(key)
        if record:
            record.status = "completed"
            record.status_code = status_code
            record.response_body = response_body
            await self._session.flush()
