"""Subset of Jira Service Management APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..auth import get_current_user
from ..store import InMemoryStore
from ..utils import paginate

router = APIRouter(tags=["Service Management"])


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


@router.get("/request")
async def list_requests(
    request: Request,
    start_at: int = Query(default=0, alias="start"),
    page_size: int = Query(default=50, alias="limit"),
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    items = store.list_service_requests()
    page = paginate(items, start_at, page_size)
    return {
        "values": page["values"],
        "size": page["total"],
        "start": page["startAt"],
        "isLast": page["isLast"],
    }


@router.post("/request", status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    service_request = store.create_service_request(payload, reporter_id=account_id)
    issue = store.issues[service_request.issue_key]
    return service_request.to_api(issue, store)


@router.get("/request/{request_id}")
async def get_request(
    request_id: str,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    service_request = store.service_requests.get(request_id)
    if not service_request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Request not found")
    issue = store.issues[service_request.issue_key]
    return service_request.to_api(issue, store)


@router.post("/request/{request_id}/approval/{approval_id}")
async def update_approval(
    request_id: str,
    approval_id: str,
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    approve = payload.get("decision", "approve").lower() == "approve"
    try:
        service_request = store.update_service_request(request_id, approval_id, approve)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    issue = store.issues[service_request.issue_key]
    return service_request.to_api(issue, store)
