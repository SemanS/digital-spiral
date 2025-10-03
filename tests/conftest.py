from __future__ import annotations

import asyncio
import threading
import time
from typing import AsyncGenerator

import pytest
import requests
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from mockjira.app import create_app
from mockjira.store import InMemoryStore
from src.infrastructure.database.models.base import Base


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


# Database fixtures for MCP tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create a test database engine."""
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


@pytest.fixture(scope="session")
async def session_factory(engine):
    """Create a session factory."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for a test.

    This fixture creates a new session for each test and rolls back
    all changes after the test completes.
    """
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
