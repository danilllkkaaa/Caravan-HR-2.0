from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.models import EmployeeDomain, RefreshTokenDomain, UserDomain
from app.infrastructure.models import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        app_env="test",
        app_debug=True,
        database_url=TEST_DATABASE_URL,
        jwt_secret_key="test-secret-key-for-jwt-signing",
        jwt_access_token_expire_minutes=15,
        jwt_refresh_token_expire_days=30,
        redis_url="redis://localhost:6379/15",
        celery_broker_url="memory://",
        celery_result_backend="cache+memory://",
        max_failed_login_attempts=5,
        account_lock_minutes=15,
        sentry_dsn="",
    )


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def sample_user() -> UserDomain:
    return UserDomain(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=hash_password("SecurePass123!"),
        is_active=True,
        failed_login_attempts=0,
        locked_until=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_employee(sample_user: UserDomain) -> EmployeeDomain:
    return EmployeeDomain(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        external_id_1c="EMP-001",
        personnel_number="P001",
        first_name="Ivan",
        last_name="Petrov",
        middle_name="Ivanovich",
        birth_date=date(1990, 1, 15),
        phone="+7-999-123-4567",
        department_id=uuid.uuid4(),
        position_id=uuid.uuid4(),
        manager_id=None,
        role="employee",
        hire_date=date(2020, 3, 1),
        work_location_id=None,
        avatar_url=None,
        sync_hash="abc123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_refresh_token(sample_user: UserDomain) -> RefreshTokenDomain:
    from app.core.security import (
        generate_refresh_token,
        hash_refresh_token,
        refresh_token_expires_at,
    )

    raw = generate_refresh_token()
    return RefreshTokenDomain(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        token_hash=hash_refresh_token(raw),
        device_info={"user_agent": "TestClient/1.0", "ip": "127.0.0.1"},
        expires_at=refresh_token_expires_at(),
        revoked_at=None,
        created_at=datetime.now(UTC),
    )


@pytest_asyncio.fixture
async def async_client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client with overridden dependencies for integration tests."""
    from app.api.deps import get_db, get_redis_client
    from app.main import app

    mock_db = AsyncMock(spec=AsyncSession)
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_redis.ping = AsyncMock(return_value=True)

    async def _override_db():
        yield mock_db

    async def _override_redis():
        return mock_redis

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_redis_client] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
