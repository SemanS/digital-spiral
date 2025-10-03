"""Issue application service."""

from __future__ import annotations

import logging
from uuid import UUID

from src.application.dtos import (
    IssueDTO,
    IssueListResponseDTO,
    IssueSearchDTO,
    IssueSyncRequestDTO,
    IssueSyncResponseDTO,
)
from src.application.use_cases import (
    GetIssueByKeyUseCase,
    GetIssuesByProjectUseCase,
    GetIssueUseCase,
    SearchIssuesUseCase,
    SyncIssueUseCase,
)

logger = logging.getLogger(__name__)


class IssueService:
    """
    Application service for issue operations.
    
    Orchestrates use cases and provides high-level API for issue management.
    """

    def __init__(
        self,
        get_issue_use_case: GetIssueUseCase,
        get_issue_by_key_use_case: GetIssueByKeyUseCase,
        search_issues_use_case: SearchIssuesUseCase,
        sync_issue_use_case: SyncIssueUseCase,
        get_issues_by_project_use_case: GetIssuesByProjectUseCase,
    ):
        """
        Initialize service.

        Args:
            get_issue_use_case: Get issue use case
            get_issue_by_key_use_case: Get issue by key use case
            search_issues_use_case: Search issues use case
            sync_issue_use_case: Sync issue use case
            get_issues_by_project_use_case: Get issues by project use case
        """
        self.get_issue_use_case = get_issue_use_case
        self.get_issue_by_key_use_case = get_issue_by_key_use_case
        self.search_issues_use_case = search_issues_use_case
        self.sync_issue_use_case = sync_issue_use_case
        self.get_issues_by_project_use_case = get_issues_by_project_use_case

    async def get_issue(self, issue_id: UUID) -> IssueDTO | None:
        """
        Get issue by ID.

        Args:
            issue_id: Issue ID

        Returns:
            Issue DTO or None if not found
        """
        logger.info(f"IssueService: Getting issue {issue_id}")
        return await self.get_issue_use_case.execute(issue_id)

    async def get_issue_by_key(self, issue_key: str) -> IssueDTO | None:
        """
        Get issue by key.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")

        Returns:
            Issue DTO or None if not found
        """
        logger.info(f"IssueService: Getting issue by key {issue_key}")
        return await self.get_issue_by_key_use_case.execute(issue_key)

    async def search_issues(
        self,
        search_dto: IssueSearchDTO,
    ) -> IssueListResponseDTO:
        """
        Search issues.

        Args:
            search_dto: Search parameters

        Returns:
            Paginated list of issues
        """
        logger.info(f"IssueService: Searching issues with {search_dto}")
        return await self.search_issues_use_case.execute(search_dto)

    async def sync_issue(
        self,
        sync_request: IssueSyncRequestDTO,
    ) -> IssueSyncResponseDTO:
        """
        Sync issue from Jira.

        Args:
            sync_request: Sync request

        Returns:
            Sync response
        """
        logger.info(f"IssueService: Syncing issue {sync_request.issue_key}")
        return await self.sync_issue_use_case.execute(sync_request)

    async def get_issues_by_project(
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
        logger.info(f"IssueService: Getting issues for project {project_key}")
        return await self.get_issues_by_project_use_case.execute(
            instance_id,
            project_key,
            skip,
            limit,
        )


__all__ = ["IssueService"]

