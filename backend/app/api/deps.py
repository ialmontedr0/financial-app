from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependencia de sesion de base de datos para FastAPI"""
    async for session in get_async_session():
        yield session
