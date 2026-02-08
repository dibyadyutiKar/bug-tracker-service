"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config.settings import settings
from app.core.database import Base, get_db
from app.core.redis import redis_client
from app.main import app
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import password_hasher


# Test database URL
TEST_DATABASE_URL = settings.database_url.replace(
    "/task_tracker", "/task_tracker_test"
)


# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""
    # Override database dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Connect Redis for tests
    await redis_client.connect()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await redis_client.disconnect()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        password_hash=password_hasher.hash("TestPass123!"),
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_manager(db_session: AsyncSession) -> User:
    """Create a test manager user."""
    user = User(
        id=uuid4(),
        username="testmanager",
        email="manager@example.com",
        password_hash=password_hasher.hash("TestPass123!"),
        role=UserRole.MANAGER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid4(),
        username="testadmin",
        email="admin@example.com",
        password_hash=password_hasher.hash("TestPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User, db_session: AsyncSession) -> dict:
    """Get authentication headers for test user."""
    from app.services.auth_service import AuthService

    auth_service = AuthService(db_session)
    tokens = await auth_service._create_tokens(test_user)

    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest_asyncio.fixture
async def manager_auth_headers(test_manager: User, db_session: AsyncSession) -> dict:
    """Get authentication headers for manager user."""
    from app.services.auth_service import AuthService

    auth_service = AuthService(db_session)
    tokens = await auth_service._create_tokens(test_manager)

    return {"Authorization": f"Bearer {tokens.access_token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(test_admin: User, db_session: AsyncSession) -> dict:
    """Get authentication headers for admin user."""
    from app.services.auth_service import AuthService

    auth_service = AuthService(db_session)
    tokens = await auth_service._create_tokens(test_admin)

    return {"Authorization": f"Bearer {tokens.access_token}"}
