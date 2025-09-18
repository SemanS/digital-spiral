"""Webhook registration and inspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status

from ..auth import get_current_user
from ..store import InMemoryStore
from ..utils import ApiError

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
        raise ApiError(status.HTTP_404_NOT_FOUND, "Webhook not found")
    store.delete_webhook(webhook_id)
    return {"status": "deleted"}


@router.get("/_mock/webhooks/deliveries")
async def list_deliveries(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return {"values": store.deliveries}


@router.get("/_mock/webhooks/logs")
async def list_logs(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return {"values": store.get_webhook_logs()}


@router.post("/_mock/webhooks/replay")
async def replay_delivery(
    request: Request,
    delivery_id: str = Query(alias="id"),
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    try:
        record = store.replay_delivery(delivery_id)
    except ValueError as exc:
        raise ApiError(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    return {"deliveryId": delivery_id, "status": record["status"]}


@router.post("/_mock/webhooks/settings")
async def update_webhook_settings(
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return store.update_webhook_settings(payload)
