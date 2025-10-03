"""Jira sync engine for data synchronization."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from src.domain.entities import Issue, Project, User
from src.infrastructure.external.jira.client import JiraClient
from src.infrastructure.external.jira.mappers import (
    JiraIssueMapper,
    JiraProjectMapper,
    JiraUserMapper,
)

logger = logging.getLogger(__name__)


class SyncStats:
    """Statistics for sync operation."""

    def __init__(self):
        self.issues_created = 0
        self.issues_updated = 0
        self.issues_deleted = 0
        self.projects_created = 0
        self.projects_updated = 0
        self.users_created = 0
        self.users_updated = 0
        self.errors = 0
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    @property
    def duration(self) -> float | None:
        """Get sync duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "issues": {
                "created": self.issues_created,
                "updated": self.issues_updated,
                "deleted": self.issues_deleted,
            },
            "projects": {
                "created": self.projects_created,
                "updated": self.projects_updated,
            },
            "users": {
                "created": self.users_created,
                "updated": self.users_updated,
            },
            "errors": self.errors,
            "duration_seconds": self.duration,
        }


class JiraSyncEngine:
    """
    Sync engine for Jira data.
    
    Handles initial full sync and incremental updates.
    """

    def __init__(
        self,
        jira_client: JiraClient,
        instance_id: UUID,
        batch_size: int = 50,
    ):
        """
        Initialize sync engine.

        Args:
            jira_client: Jira API client
            instance_id: Jira instance ID
            batch_size: Number of items to fetch per batch
        """
        self.jira_client = jira_client
        self.instance_id = instance_id
        self.batch_size = batch_size

    async def full_sync(self) -> SyncStats:
        """
        Perform full sync of all data.

        Returns:
            Sync statistics
        """
        stats = SyncStats()
        stats.start_time = datetime.utcnow()

        logger.info(f"Starting full sync for instance {self.instance_id}")

        try:
            # Sync projects first
            await self._sync_projects(stats)

            # Sync users
            await self._sync_users(stats)

            # Sync issues
            await self._sync_issues(stats)

        except Exception as e:
            logger.error(f"Full sync error: {e}", exc_info=True)
            stats.errors += 1

        stats.end_time = datetime.utcnow()
        logger.info(f"Full sync completed: {stats.to_dict()}")

        return stats

    async def incremental_sync(
        self,
        since: datetime | None = None,
    ) -> SyncStats:
        """
        Perform incremental sync of updated data.

        Args:
            since: Sync changes since this timestamp (default: last hour)

        Returns:
            Sync statistics
        """
        stats = SyncStats()
        stats.start_time = datetime.utcnow()

        if since is None:
            since = datetime.utcnow() - timedelta(hours=1)

        logger.info(
            f"Starting incremental sync for instance {self.instance_id} "
            f"since {since.isoformat()}"
        )

        try:
            # Sync updated issues
            await self._sync_updated_issues(stats, since)

        except Exception as e:
            logger.error(f"Incremental sync error: {e}", exc_info=True)
            stats.errors += 1

        stats.end_time = datetime.utcnow()
        logger.info(f"Incremental sync completed: {stats.to_dict()}")

        return stats

    async def sync_project(self, project_key: str) -> Project:
        """
        Sync a single project.

        Args:
            project_key: Project key

        Returns:
            Synced project entity
        """
        logger.info(f"Syncing project: {project_key}")

        # Fetch from Jira
        jira_data = await self.jira_client.get_project(project_key)

        # Map to entity
        project = JiraProjectMapper.to_entity(jira_data, self.instance_id)

        # TODO: Save to database via repository

        return project

    async def sync_issue(self, issue_key: str) -> Issue:
        """
        Sync a single issue.

        Args:
            issue_key: Issue key

        Returns:
            Synced issue entity
        """
        logger.info(f"Syncing issue: {issue_key}")

        # Fetch from Jira with changelog
        jira_data = await self.jira_client.get_issue(
            issue_key,
            expand=["changelog", "renderedFields"]
        )

        # Map to entity
        issue = JiraIssueMapper.to_entity(jira_data, self.instance_id)

        # TODO: Save to database via repository
        # TODO: Sync comments and changelog

        return issue

    async def _sync_projects(self, stats: SyncStats):
        """Sync all projects."""
        logger.info("Syncing projects...")

        start_at = 0
        while True:
            # Fetch batch
            projects = await self.jira_client.get_all_projects(
                start_at=start_at,
                max_results=self.batch_size,
            )

            if not projects:
                break

            # Process each project
            for jira_project in projects:
                try:
                    project = JiraProjectMapper.to_entity(
                        jira_project,
                        self.instance_id
                    )

                    # TODO: Check if exists and update or create
                    stats.projects_created += 1

                except Exception as e:
                    logger.error(f"Error syncing project: {e}")
                    stats.errors += 1

            # Next batch
            start_at += len(projects)

            # Break if we got less than batch size
            if len(projects) < self.batch_size:
                break

        logger.info(f"Synced {stats.projects_created} projects")

    async def _sync_users(self, stats: SyncStats):
        """Sync users from issues."""
        logger.info("Syncing users...")

        # Note: Jira doesn't have a direct "get all users" endpoint
        # We'll collect users from issues and projects
        # This is a simplified implementation

        # TODO: Implement user collection from issues
        # For now, we'll sync users as we encounter them in issues

        logger.info("User sync will be done during issue sync")

    async def _sync_issues(self, stats: SyncStats):
        """Sync all issues."""
        logger.info("Syncing issues...")

        start_at = 0
        while True:
            # Build JQL query for all issues
            jql = "ORDER BY updated DESC"

            # Fetch batch
            result = await self.jira_client.search_issues(
                jql=jql,
                start_at=start_at,
                max_results=self.batch_size,
                expand=["changelog"],
            )

            issues = result.get("issues", [])
            if not issues:
                break

            # Process each issue
            for jira_issue in issues:
                try:
                    issue = JiraIssueMapper.to_entity(
                        jira_issue,
                        self.instance_id
                    )

                    # TODO: Check if exists and update or create
                    stats.issues_created += 1

                    # Sync assignee and reporter
                    await self._sync_user_from_issue(jira_issue, stats)

                except Exception as e:
                    logger.error(f"Error syncing issue: {e}")
                    stats.errors += 1

            # Next batch
            start_at += len(issues)

            # Break if we got less than batch size
            if len(issues) < self.batch_size:
                break

        logger.info(f"Synced {stats.issues_created} issues")

    async def _sync_updated_issues(self, stats: SyncStats, since: datetime):
        """Sync issues updated since timestamp."""
        logger.info(f"Syncing issues updated since {since.isoformat()}...")

        start_at = 0
        # Format datetime for JQL
        since_str = since.strftime("%Y-%m-%d %H:%M")

        while True:
            # Build JQL query for updated issues
            jql = f"updated >= '{since_str}' ORDER BY updated DESC"

            # Fetch batch
            result = await self.jira_client.search_issues(
                jql=jql,
                start_at=start_at,
                max_results=self.batch_size,
                expand=["changelog"],
            )

            issues = result.get("issues", [])
            if not issues:
                break

            # Process each issue
            for jira_issue in issues:
                try:
                    issue = JiraIssueMapper.to_entity(
                        jira_issue,
                        self.instance_id
                    )

                    # TODO: Check if exists and update or create
                    stats.issues_updated += 1

                except Exception as e:
                    logger.error(f"Error syncing issue: {e}")
                    stats.errors += 1

            # Next batch
            start_at += len(issues)

            # Break if we got less than batch size
            if len(issues) < self.batch_size:
                break

        logger.info(f"Synced {stats.issues_updated} updated issues")

    async def _sync_user_from_issue(self, jira_issue: dict, stats: SyncStats):
        """Sync users from issue (assignee, reporter)."""
        fields = jira_issue.get("fields", {})

        # Sync assignee
        assignee = fields.get("assignee")
        if assignee:
            try:
                user = JiraUserMapper.to_entity(assignee, self.instance_id)
                # TODO: Save to database
                stats.users_created += 1
            except Exception as e:
                logger.error(f"Error syncing assignee: {e}")

        # Sync reporter
        reporter = fields.get("reporter")
        if reporter:
            try:
                user = JiraUserMapper.to_entity(reporter, self.instance_id)
                # TODO: Save to database
                stats.users_created += 1
            except Exception as e:
                logger.error(f"Error syncing reporter: {e}")


__all__ = ["JiraSyncEngine", "SyncStats"]

