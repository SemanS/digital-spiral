"""Issue REST API endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.dtos import (
    IssueDTO,
    IssueListResponseDTO,
    IssueSearchDTO,
    IssueSyncRequestDTO,
    IssueSyncResponseDTO,
)
from src.application.services import IssueService
from src.application.validation import IssueKeyValidator, ValidationException
from src.interfaces.rest.dependencies import get_issue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("/{issue_id}", response_model=IssueDTO)
async def get_issue(
    issue_id: UUID,
    service: IssueService = Depends(get_issue_service),
):
    """
    Get issue by ID.

    Args:
        issue_id: Issue UUID
        service: Issue service

    Returns:
        Issue DTO

    Raises:
        HTTPException: If issue not found
    """
    logger.info(f"GET /issues/{issue_id}")

    issue = await service.get_issue(issue_id)

    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_id} not found",
        )

    return issue


@router.get("/key/{issue_key}", response_model=IssueDTO)
async def get_issue_by_key(
    issue_key: str,
    service: IssueService = Depends(get_issue_service),
):
    """
    Get issue by key.

    Args:
        issue_key: Issue key (e.g., "PROJ-123")
        service: Issue service

    Returns:
        Issue DTO

    Raises:
        HTTPException: If issue not found or invalid key
    """
    logger.info(f"GET /issues/key/{issue_key}")

    # Validate issue key
    try:
        IssueKeyValidator.validate(issue_key)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )

    issue = await service.get_issue_by_key(issue_key)

    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue {issue_key} not found",
        )

    return issue


@router.get("/", response_model=IssueListResponseDTO)
async def search_issues(
    instance_id: UUID = Query(..., description="Jira instance ID"),
    project_key: str | None = Query(None, description="Project key"),
    status: str | None = Query(None, description="Issue status"),
    assignee_account_id: str | None = Query(None, description="Assignee account ID"),
    issue_type: str | None = Query(None, description="Issue type"),
    priority: str | None = Query(None, description="Priority"),
    query: str | None = Query(None, description="Search query"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    service: IssueService = Depends(get_issue_service),
):
    """
    Search issues.

    Args:
        instance_id: Jira instance ID
        project_key: Filter by project key
        status: Filter by status
        assignee_account_id: Filter by assignee
        issue_type: Filter by issue type
        priority: Filter by priority
        query: Text search query
        skip: Pagination offset
        limit: Pagination limit
        service: Issue service

    Returns:
        Paginated list of issues
    """
    logger.info(f"GET /issues?instance_id={instance_id}&skip={skip}&limit={limit}")

    search_dto = IssueSearchDTO(
        instance_id=instance_id,
        project_key=project_key,
        status=status,
        assignee_account_id=assignee_account_id,
        issue_type=issue_type,
        priority=priority,
        query=query,
        skip=skip,
        limit=limit,
    )

    return await service.search_issues(search_dto)


@router.get("/project/{project_key}", response_model=IssueListResponseDTO)
async def get_issues_by_project(
    project_key: str,
    instance_id: UUID = Query(..., description="Jira instance ID"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return"),
    service: IssueService = Depends(get_issue_service),
):
    """
    Get issues by project.

    Args:
        project_key: Project key
        instance_id: Jira instance ID
        skip: Pagination offset
        limit: Pagination limit
        service: Issue service

    Returns:
        Paginated list of issues
    """
    logger.info(f"GET /issues/project/{project_key}")

    return await service.get_issues_by_project(
        instance_id=instance_id,
        project_key=project_key,
        skip=skip,
        limit=limit,
    )


@router.post("/sync", response_model=IssueSyncResponseDTO)
async def sync_issue(
    sync_request: IssueSyncRequestDTO,
    service: IssueService = Depends(get_issue_service),
):
    """
    Sync issue from Jira.

    Args:
        sync_request: Sync request
        service: Issue service

    Returns:
        Sync response with synced issue
    """
    logger.info(f"POST /issues/sync - {sync_request.issue_key}")

    # Validate issue key
    try:
        IssueKeyValidator.validate(sync_request.issue_key)
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )

    try:
        return await service.sync_issue(sync_request)
    except Exception as e:
        logger.error(f"Failed to sync issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync issue: {str(e)}",
        )


__all__ = ["router"]

