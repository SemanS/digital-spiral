"""Subset of Jira Software (agile) APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status

from ..auth import get_current_user
from ..store import InMemoryStore
from ..utils import ApiError, paginate

router = APIRouter(tags=["Agile"])


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


@router.get("/board")
async def list_boards(
    request: Request,
    start_at: int = Query(default=0, alias="startAt"),
    max_results: int = Query(default=50, alias="maxResults"),
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    page = paginate(store.list_boards(), start_at, max_results)
    return {
        "startAt": page["startAt"],
        "maxResults": page["maxResults"],
        "total": page["total"],
        "isLast": page["isLast"],
        "values": page["values"],
    }


@router.get("/board/{board_id}/sprint")
async def list_sprints(
    board_id: int,
    request: Request,
    start_at: int = Query(default=0, alias="startAt"),
    max_results: int = Query(default=50, alias="maxResults"),
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    sprints = store.list_sprints(board_id)
    page = paginate(sprints, start_at, max_results)
    return {
        "startAt": page["startAt"],
        "maxResults": page["maxResults"],
        "total": page["total"],
        "isLast": page["isLast"],
        "values": page["values"],
    }


@router.post("/sprint", status_code=status.HTTP_201_CREATED)
async def create_sprint(
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    sprint = store.create_sprint(payload)
    return sprint.to_api()


@router.get("/board/{board_id}/backlog")
async def backlog(
    board_id: int,
    request: Request,
    start_at: int = Query(default=0, alias="startAt"),
    max_results: int = Query(default=50, alias="maxResults"),
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    if board_id not in store.boards:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Board not found")
    issues = store.backlog_issues(board_id)
    page = paginate([issue.to_api(store) for issue in issues], start_at, max_results)
    return {
        "startAt": page["startAt"],
        "maxResults": page["maxResults"],
        "total": page["total"],
        "isLast": page["isLast"],
        "issues": page["values"],
    }
