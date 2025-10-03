"""Issue repository interface."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from uuid import UUID

from src.domain.entities import Issue

from .repository import IRepository


class IIssueRepository(IRepository[Issue]):
    """
    Issue repository interface.

    Defines operations specific to Issue entities.
    """

    @abstractmethod
    async def get_by_key(self, issue_key: str) -> Issue | None:
        """
        Get issue by key (e.g., "PROJ-123").

        Args:
            issue_key: Issue key

        Returns:
            Issue or None if not found
        """
        pass

    @abstractmethod
    async def get_by_instance(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """
        Get all issues for a Jira instance.

        Args:
            instance_id: Jira instance ID
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issues
        """
        pass

    @abstractmethod
    async def get_by_project(
        self,
        instance_id: UUID,
        project_key: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """
        Get all issues for a project.

        Args:
            instance_id: Jira instance ID
            project_key: Project key
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issues
        """
        pass

    @abstractmethod
    async def get_by_assignee(
        self,
        instance_id: UUID,
        assignee_account_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """
        Get all issues assigned to a user.

        Args:
            instance_id: Jira instance ID
            assignee_account_id: Assignee account ID
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issues
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        instance_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """
        Get all issues with a specific status.

        Args:
            instance_id: Jira instance ID
            status: Issue status
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issues
        """
        pass

    @abstractmethod
    async def get_updated_since(
        self,
        instance_id: UUID,
        since: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """
        Get all issues updated since a specific time.

        Args:
            instance_id: Jira instance ID
            since: Timestamp to filter from
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issues
        """
        pass

    @abstractmethod
    async def search(
        self,
        instance_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """
        Search issues by text query.

        Args:
            instance_id: Jira instance ID
            query: Search query
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of matching issues
        """
        pass

    @abstractmethod
    async def bulk_create(self, issues: list[Issue]) -> list[Issue]:
        """
        Create multiple issues in bulk.

        Args:
            issues: List of issues to create

        Returns:
            List of created issues
        """
        pass

    @abstractmethod
    async def bulk_update(self, issues: list[Issue]) -> list[Issue]:
        """
        Update multiple issues in bulk.

        Args:
            issues: List of issues to update

        Returns:
            List of updated issues
        """
        pass


__all__ = ["IIssueRepository"]

