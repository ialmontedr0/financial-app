"""Debug test hang."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import get_settings

settings = get_settings()
test_url = settings.DATABASE_URL.replace("/fip", "/fip_test")

async def test_query():
    engine = create_async_engine(test_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(text('SELECT COUNT(*) FROM "user"'))
        count = result.scalar()
        print(f"Users: {count}")

        result = await session.execute(text('SELECT COUNT(*) FROM financial_account'))
        count = result.scalar()
        print(f"Accounts: {count}")

        result = await session.execute(text("SELECT COUNT(*) FROM transaction"))
        count = result.scalar()
        print(f"Transactions: {count}")

    await engine.dispose()
    print("DB query OK")

asyncio.run(test_query())
