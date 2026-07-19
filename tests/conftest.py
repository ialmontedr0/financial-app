from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.infrastructure.db.base import Base
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.password_hasher import PasswordHasher
from app.main import create_app

settings = get_settings()

TEST_DATABASE_URL = settings.DATABASE_URL.replace("/fip", "/fip_test")


@pytest_asyncio.fixture(loop_scope="session")
async def test_engine():
    """Create test database engine (shared across all tests)."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed system categories into the test database
    from app.infrastructure.seed.category_seed import seed_system_categories

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        async with session.begin():
            await seed_system_categories(session)

    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(loop_scope="session")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession]:
    """Create a fresh database session for each test."""
    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(loop_scope="session")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Create async test client with DB session override."""
    app = create_app()

    async def override_get_db():
        yield db_session

    from app.api.deps import get_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_password() -> str:
    """A valid test password."""
    return "TestPassword123!"


@pytest.fixture
def test_email() -> str:
    """A valid test email."""
    return "test@example.com"


@pytest.fixture
def hashed_password(test_password: str) -> str:
    """A pre-hashed test password."""
    return PasswordHasher.hash_password(test_password)


@pytest.fixture
def valid_access_token() -> str:
    """Generate a valid access token for testing."""
    return JWTService.create_access_token("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def valid_refresh_token() -> str:
    """Generate a valid refresh token for testing."""
    return JWTService.create_refresh_token("00000000-0000-0000-0000-000000000001")
