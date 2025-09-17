"""Administrative endpoints for mock Jira diagnostics and seed control."""

from __future__ import annotations

from importlib import metadata

from fastapi import APIRouter, Request

from ..store import InMemoryStore

router = APIRouter(tags=["Mock"])


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


@router.get("/_mock/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/_mock/info")
async def info(request: Request) -> dict:
    store = get_store(request)
    try:
        version = metadata.version("mock-jira-server")
    except metadata.PackageNotFoundError:  # pragma: no cover - fallback for editable installs
        version = request.app.version
    seed = {
        "projects": len(store.projects),
        "users": len(store.users),
        "issues": len(store.issues),
        "webhooks": len(store.webhooks),
    }
    return {"version": version, "seed": seed}


@router.get("/_mock/seed/export")
async def export_seed(request: Request) -> dict:
    store = get_store(request)
    return store.export_seed()


@router.post("/_mock/seed/import")
async def import_seed(request: Request, payload: dict) -> dict:
    store = get_store(request)
    store.import_seed(payload)
    return {"status": "imported", "issues": len(store.issues)}


@router.get("/_mock/trace/{request_id}")
async def trace(request: Request, request_id: str) -> dict:
    entries = [
        entry for entry in request.app.state.request_log if entry["id"] == request_id
    ]
    return {"entries": entries}
