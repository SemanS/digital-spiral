"""Subset of the Jira platform REST API implemented for the mock server."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status

from ..auth import get_current_user
from ..store import InMemoryStore
from ..utils import ApiError, paginate, parse_jql

router = APIRouter(tags=["Platform"])


def get_store(request: Request) -> InMemoryStore:
    return request.app.state.store


@router.get("/project")
async def list_projects(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return {"values": store.list_projects()}


@router.get("/field")
async def list_fields(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return {"values": store.fields_payload()}


@router.get("/status")
async def list_statuses(
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    return {"values": get_store(request).list_statuses()}


@router.get("/issue/{issue_id_or_key}")
async def get_issue(
    issue_id_or_key: str,
    request: Request,
    expand: str | None = Query(default=None),
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    issue = store.get_issue(issue_id_or_key)
    if not issue:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Issue not found")
    expand_set = {segment.strip() for segment in expand.split(",") if segment.strip()} if expand else None
    return issue.to_api(store, expand=expand_set)


@router.post("/issue", status_code=status.HTTP_201_CREATED)
async def create_issue(
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    try:
        issue = store.create_issue(payload, reporter_id=account_id)
    except ValueError as exc:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            str(exc),
        ) from exc
    return issue.to_api(store)


@router.post("/issueLink", status_code=status.HTTP_201_CREATED)
async def create_issue_link(
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    try:
        return store.create_issue_link(payload, account_id)
    except ValueError as exc:
        raise ApiError(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.put("/issue/{issue_id_or_key}")
async def update_issue(
    issue_id_or_key: str,
    payload: dict,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    issue = store.get_issue(issue_id_or_key)
    if not issue:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Issue not found")
    issue = store.update_issue(issue_id_or_key, payload)
    return issue.to_api(store)


async def _search_impl(
    request: Request,
    jql: str | None,
    start_at: int,
    max_results: int,
    account_id: str,
) -> dict:
    store = get_store(request)
    try:
        parsed = parse_jql(jql)
    except ValueError as exc:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "Error in JQL",
            field_errors={"jql": str(exc)},
        ) from exc
    filters = parsed["filters"]
    order_by = parsed["order_by"]

    def _convert_assignee(value: str) -> str:
        if value.lower() == "currentuser()":
            return account_id
        if value.lower() == "unassigned":
            return "unassigned"
        return value

    assignee_filter = filters.get("assignee")
    if isinstance(assignee_filter, list):
        filters["assignee"] = [_convert_assignee(v) for v in assignee_filter]
    elif isinstance(assignee_filter, str):
        filters["assignee"] = _convert_assignee(assignee_filter)

    results = store.search_issues(filters, order_by=order_by)
    page = paginate(results, start_at, max_results)
    return {
        "startAt": page["startAt"],
        "maxResults": page["maxResults"],
        "total": page["total"],
        "isLast": page["isLast"],
        "issues": [issue.to_api(store) for issue in page["values"]],
    }


@router.get("/search")
async def search_issues(
    request: Request,
    jql: str | None = Query(default=None),
    start_at: int = Query(default=0, alias="startAt"),
    max_results: int = Query(default=50, alias="maxResults"),
    account_id: str = Depends(get_current_user),
) -> dict:
    return await _search_impl(request, jql, start_at, max_results, account_id)


@router.post("/search")
async def search_issues_post(
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    jql = payload.get("jql")
    start_at = payload.get("startAt", 0)
    max_results = payload.get("maxResults", 50)
    return await _search_impl(request, jql, start_at, max_results, account_id)


@router.get("/issue/{issue_id_or_key}/transitions")
async def list_transitions(
    issue_id_or_key: str,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    issue = store.get_issue(issue_id_or_key)
    if not issue:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Issue not found")
    transitions = store.get_transitions(issue)
    return {"transitions": [t.to_api() for t in transitions]}


@router.post("/issue/{issue_id_or_key}/transitions")
async def apply_transition(
    issue_id_or_key: str,
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    issue = store.get_issue(issue_id_or_key)
    if not issue:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Issue not found")
    transition_data = payload.get("transition", {})
    transition_id = transition_data.get("id")
    if not transition_id:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "Transition id is required",
            field_errors={"transition.id": "Missing transition id"},
        )
    try:
        issue = store.apply_transition(issue, transition_id, account_id)
    except ValueError as exc:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "Transition not allowed",
            field_errors={"transition.id": str(exc)},
        ) from exc
    return {"issue": issue.to_api(store)}


@router.get("/issue/{issue_id_or_key}/comment")
async def list_comments(
    issue_id_or_key: str,
    request: Request,
    _: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    issue = store.get_issue(issue_id_or_key)
    if not issue:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Issue not found")
    comments = [
        comment.to_api(store.users[comment.author_id]) for comment in issue.comments
    ]
    return {
        "startAt": 0,
        "maxResults": len(comments),
        "total": len(comments),
        "comments": comments,
    }


@router.post("/issue/{issue_id_or_key}/comment", status_code=status.HTTP_201_CREATED)
async def create_comment(
    issue_id_or_key: str,
    payload: dict,
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    issue = store.get_issue(issue_id_or_key)
    if not issue:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Issue not found")
    body = payload.get("body")
    if not body:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "Comment body is required",
            field_errors={"body": "Missing body"},
        )
    comment = store.add_comment(issue, author_id=account_id, body=body)
    return comment.to_api(store.users[account_id])


@router.get("/myself")
async def get_myself(
    request: Request,
    account_id: str = Depends(get_current_user),
) -> dict:
    store = get_store(request)
    return store.users[account_id].to_api()
