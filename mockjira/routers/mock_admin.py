"""Administrative endpoints for mock Jira diagnostics and seed control."""

from __future__ import annotations

from importlib import metadata

from fastapi import APIRouter, Request

from ..auth import auth_dependency, get_current_user
from ..fixtures.generator import GenConfig, generate_store
from ..store import InMemoryStore

router = APIRouter(tags=["Mock"])


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


def _counts(store: InMemoryStore) -> dict[str, int]:
    return {
        "projects": len(store.projects),
        "issues": len(store.issues),
        "users": len(store.users),
        "boards": len(store.boards),
        "sprints": len(store.sprints),
        "requests": len(store.service_requests),
    }


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
    signature = {
        "version": store.webhook_signature_version,
        "legacyCompat": store.webhook_signature_compat,
    }
    return {"version": version, "seed": seed, "webhookSignature": signature}


@router.get("/_mock/seed/export")
async def export_seed(request: Request) -> dict:
    store = get_store(request)
    return store.export_seed()


@router.post("/_mock/seed/import")
async def import_seed(request: Request, payload: dict) -> dict:
    store = get_store(request)
    store.import_seed(payload)
    return {"status": "imported", "counts": _counts(store)}


@router.post("/_mock/seed/load")
async def load_seed(request: Request, payload: dict) -> dict:
    store = get_store(request)
    store.import_seed(payload)
    return {"status": "loaded", "counts": _counts(store)}


@router.post("/_mock/seed/generate")
async def generate_seed(request: Request, payload: dict | None = None) -> dict:
    body = payload or {}
    cfg_kwargs = {
        key: body[key]
        for key in GenConfig.__annotations__.keys()
        if key in body
    }
    cfg = GenConfig(**cfg_kwargs)
    store = generate_store(cfg)
    request.app.state.store = store
    request.app.dependency_overrides[get_current_user] = auth_dependency(store)
    return {"status": "ok", "counts": _counts(store)}


@router.get("/_mock/trace/{request_id}")
async def trace(request: Request, request_id: str) -> dict:
    entries = [
        entry for entry in request.app.state.request_log if entry["id"] == request_id
    ]
    return {"entries": entries}
