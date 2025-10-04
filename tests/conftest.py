from __future__ import annotations

import threading
import time
import asyncio
from uuid import UUID
from typing import AsyncGenerator

import pytest
import requests
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from mockjira.app import create_app
from mockjira.store import InMemoryStore
from src.infrastructure.database.base import Base


@pytest.fixture()
def live_server() -> str:
    """Run the mock Jira server in the background for integration tests."""

    store = InMemoryStore.with_seed_data()
    app = create_app(store)
    config = uvicorn.Config(app, host="127.0.0.1", port=9000, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5
    url = "http://127.0.0.1:9000/_mock/health"
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=0.25)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.1)
    else:  # pragma: no cover - guard for flaky environments
        server.should_exit = True
        thread.join(timeout=5)
        raise RuntimeError("Mock Jira server failed to start")

    yield "http://127.0.0.1:9000"

    server.should_exit = True
    thread.join(timeout=5)


# Analytics test fixtures

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async database session for tests."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_tenant_id() -> UUID:
    """Get test tenant ID."""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def test_instance_id() -> UUID:
    """Get test instance ID."""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def test_user_id() -> str:
    """Get test user ID."""
    return "test-user-123"


@pytest.fixture
async def async_client():
    """Create async HTTP client for API tests."""
    from httpx import AsyncClient
    from src.api.main import app  # Assuming you have a FastAPI app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
