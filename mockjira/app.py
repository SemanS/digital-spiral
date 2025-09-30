"""Application factory for the mock Jira server."""

from __future__ import annotations

import json
import logging
import uuid
from collections import deque
from datetime import datetime, timezone

# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from fastapi import FastAPI, Request

from .auth import auth_dependency, get_current_user
from .routers import agile, mock_admin, platform, service_management, webhooks
from .store import InMemoryStore
from .utils import ApiError


logger = logging.getLogger("mockjira.access")


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

    @app.exception_handler(ApiError)
    async def _handle_api_error(_: Request, exc: ApiError):  # pragma: no cover - FastAPI wiring
        return exc.to_response()
    app.state.request_log = deque(maxlen=500)

    @app.middleware("http")
    async def _request_id_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Req-Id") or str(uuid.uuid4())
        request.state.req_id = req_id
        start = datetime.now(UTC)
        response = await call_next(request)
        duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
        response.headers["X-Req-Id"] = req_id
        entry = {
            "id": req_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "timestamp": start.isoformat(),
        }
        app.state.request_log.append(entry)
        log_entry = {
            **entry,
            "message": "request",
        }
        logger.info(json.dumps(log_entry))
        return response

    app.include_router(platform.router, prefix="/rest/api/3")
    app.include_router(agile.router, prefix="/rest/agile/1.0")
    app.include_router(service_management.router, prefix="/rest/servicedeskapi")
    app.include_router(webhooks.router, prefix="/rest/api/3")
    app.include_router(mock_admin.router)

    app.state.store = store

    return app
