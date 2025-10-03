"""Issue use cases."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from src.application.dtos import (
    IssueDTO,
    IssueListResponseDTO,
    IssueSearchDTO,
    IssueSyncRequestDTO,
    IssueSyncResponseDTO,
)
from src.application.interfaces import IIssueRepository
from src.domain.entities import Issue
from src.infrastructure.external.jira import JiraClient
from src.infrastructure.external.jira.mappers import JiraIssueMapper

logger = logging.getLogger(__name__)


class GetIssueUseCase:
    """Use case for getting an issue by ID."""

    def __init__(self, issue_repository: IIssueRepository):
        """
        Initialize use case.

        Args:
            issue_repository: Issue repository
        """
        self.issue_repository = issue_repository

    async def execute(self, issue_id: UUID) -> IssueDTO | None:
        """
        Get issue by ID.

        Args:
            issue_id: Issue ID

        Returns:
            Issue DTO or None if not found
        """
        logger.info(f"Getting issue: {issue_id}")

        issue = await self.issue_repository.get_by_id(issue_id)

        if issue is None:
            return None

        return IssueDTO.model_validate(issue)


class GetIssueByKeyUseCase:
    """Use case for getting an issue by key."""

    def __init__(self, issue_repository: IIssueRepository):
        """
        Initialize use case.

        Args:
            issue_repository: Issue repository
        """
        self.issue_repository = issue_repository

    async def execute(self, issue_key: str) -> IssueDTO | None:
        """
        Get issue by key.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")

        Returns:
            Issue DTO or None if not found
        """
        logger.info(f"Getting issue by key: {issue_key}")

        issue = await self.issue_repository.get_by_key(issue_key)

        if issue is None:
            return None

        return IssueDTO.model_validate(issue)


class SearchIssuesUseCase:
    """Use case for searching issues."""

    def __init__(self, issue_repository: IIssueRepository):
        """
        Initialize use case.

        Args:
            issue_repository: Issue repository
        """
        self.issue_repository = issue_repository

    async def execute(self, search_dto: IssueSearchDTO) -> IssueListResponseDTO:
        """
        Search issues.

        Args:
            search_dto: Search parameters

        Returns:
            Paginated list of issues
        """
        logger.info(f"Searching issues: {search_dto}")

        # Build search based on criteria
        if search_dto.query:
            # Text search
            issues = await self.issue_repository.search(
                search_dto.instance_id,
                search_dto.query,
                skip=search_dto.skip,
                limit=search_dto.limit,
            )
        elif search_dto.project_key:
            # Search by project
            issues = await self.issue_repository.get_by_project(
                search_dto.instance_id,
                search_dto.project_key,
                skip=search_dto.skip,
                limit=search_dto.limit,
            )
        elif search_dto.assignee_account_id:
            # Search by assignee
            issues = await self.issue_repository.get_by_assignee(
                search_dto.instance_id,
                search_dto.assignee_account_id,
                skip=search_dto.skip,
                limit=search_dto.limit,
            )
        elif search_dto.status:
            # Search by status
            issues = await self.issue_repository.get_by_status(
                search_dto.instance_id,
                search_dto.status,
                skip=search_dto.skip,
                limit=search_dto.limit,
            )
        else:
            # Get all for instance
            issues = await self.issue_repository.get_by_instance(
                search_dto.instance_id,
                skip=search_dto.skip,
                limit=search_dto.limit,
            )

        # Get total count
        total = await self.issue_repository.count()

        # Convert to DTOs
        issue_dtos = [IssueDTO.model_validate(issue) for issue in issues]

        return IssueListResponseDTO(
            items=issue_dtos,
            total=total,
            skip=search_dto.skip,
            limit=search_dto.limit,
            has_more=(search_dto.skip + len(issue_dtos)) < total,
        )


class SyncIssueUseCase:
    """Use case for syncing an issue from Jira."""

    def __init__(
        self,
        issue_repository: IIssueRepository,
        jira_client: JiraClient,
    ):
        """
        Initialize use case.

        Args:
            issue_repository: Issue repository
            jira_client: Jira API client
        """
        self.issue_repository = issue_repository
        self.jira_client = jira_client

    async def execute(
        self,
        sync_request: IssueSyncRequestDTO,
    ) -> IssueSyncResponseDTO:
        """
        Sync issue from Jira.

        Args:
            sync_request: Sync request

        Returns:
            Sync response with synced issue
        """
        logger.info(f"Syncing issue: {sync_request.issue_key}")

        # Fetch from Jira
        jira_data = await self.jira_client.get_issue(
            sync_request.issue_key,
            expand=["changelog", "renderedFields"],
        )

        # Map to entity
        issue = JiraIssueMapper.to_entity(jira_data, sync_request.instance_id)

        # Check if issue exists
        existing = await self.issue_repository.get_by_key(sync_request.issue_key)

        if existing:
            # Update existing
            issue.id = existing.id
            updated_issue = await self.issue_repository.update(issue)
            logger.info(f"Updated issue: {sync_request.issue_key}")
        else:
            # Create new
            updated_issue = await self.issue_repository.create(issue)
            logger.info(f"Created issue: {sync_request.issue_key}")

        # TODO: Sync comments and changelog

        return IssueSyncResponseDTO(
            issue=IssueDTO.model_validate(updated_issue),
            synced_at=datetime.utcnow(),
            comments_synced=0,
            changelogs_synced=0,
        )


class GetIssuesByProjectUseCase:
    """Use case for getting issues by project."""

    def __init__(self, issue_repository: IIssueRepository):
        """
        Initialize use case.

        Args:
            issue_repository: Issue repository
        """
        self.issue_repository = issue_repository

    async def execute(
        self,
        instance_id: UUID,
        project_key: str,
        skip: int = 0,
        limit: int = 50,
    ) -> IssueListResponseDTO:
        """
        Get issues by project.

        Args:
            instance_id: Jira instance ID
            project_key: Project key
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            Paginated list of issues
        """
        logger.info(f"Getting issues for project: {project_key}")

        issues = await self.issue_repository.get_by_project(
            instance_id,
            project_key,
            skip=skip,
            limit=limit,
        )

        total = await self.issue_repository.count()

        issue_dtos = [IssueDTO.model_validate(issue) for issue in issues]

        return IssueListResponseDTO(
            items=issue_dtos,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(issue_dtos)) < total,
        )


__all__ = [
    "GetIssueUseCase",
    "GetIssueByKeyUseCase",
    "SearchIssuesUseCase",
    "SyncIssueUseCase",
    "GetIssuesByProjectUseCase",
]

