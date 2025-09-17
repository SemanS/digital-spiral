"""Webhook registration and inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import get_current_user
from ..store import InMemoryStore

router = APIRouter(tags=["Webhooks"])


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


@router.post("/webhook", status_code=status.HTTP_201_CREATED)
async def register_webhook(
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return {"webhookRegistrationResult": store.register_webhook(payload)}


@router.get("/webhook")
async def list_webhook(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return {"values": store.list_webhooks()}


@router.delete("/webhook/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    if webhook_id not in store.webhooks:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    store.delete_webhook(webhook_id)
    return {"status": "deleted"}


@router.get("/_mock/webhooks/deliveries")
async def list_deliveries(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return {"values": store.deliveries}
