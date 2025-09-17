"""Application factory for the mock Jira server."""

from __future__ import annotations

from fastapi import FastAPI

from .auth import auth_dependency, get_current_user
from .routers import agile, platform, service_management, webhooks
from .store import InMemoryStore


def create_app(store: InMemoryStore | None = None) -> FastAPI:
    """Create a FastAPI instance configured with all routes.

    Parameters
    ----------
    store:
        Optional :class:`InMemoryStore` instance. When ``None`` a new store with
        seeded data is created. Passing a custom store is useful for testing.
    """

    store = store or InMemoryStore.with_seed_data()

    app = FastAPI(
        title="Mock Jira Cloud",
        version="0.1.0",
        description=(
            "Stateful mock implementation of popular Jira Cloud API surfaces."
        ),
    )

    app.dependency_overrides[get_current_user] = auth_dependency(store)
    app.include_router(platform.router, prefix="/rest/api/3")
    app.include_router(agile.router, prefix="/rest/agile/1.0")
    app.include_router(service_management.router, prefix="/rest/servicedeskapi")
    app.include_router(webhooks.router, prefix="/rest/api/3")

    app.state.store = store

    return app
