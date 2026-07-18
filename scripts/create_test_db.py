import asyncpg
import asyncio


async def create_db():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/postgres")
    exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname = 'fip_test'"
    )
    if not exists:
        await conn.execute("CREATE DATABASE fip_test")
        print("Created fip_test")
    else:
        print("fip_test already exists")
    await conn.close()


asyncio.run(create_db())
