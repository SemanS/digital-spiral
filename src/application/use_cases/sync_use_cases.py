"""Sync use cases."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from src.application.dtos import (
    FullSyncRequestDTO,
    FullSyncResponseDTO,
    IncrementalSyncRequestDTO,
    IncrementalSyncResponseDTO,
    SyncStatsDTO,
    SyncStatusDTO,
)
from src.infrastructure.external.jira import JiraClient
from src.infrastructure.external.jira.sync_engine import JiraSyncEngine

logger = logging.getLogger(__name__)


class FullSyncUseCase:
    """Use case for performing full Jira sync."""

    def __init__(self, jira_client: JiraClient):
        """
        Initialize use case.

        Args:
            jira_client: Jira API client
        """
        self.jira_client = jira_client

    async def execute(
        self,
        request: FullSyncRequestDTO,
    ) -> FullSyncResponseDTO:
        """
        Perform full sync.

        Args:
            request: Full sync request

        Returns:
            Sync response with statistics
        """
        logger.info(f"Starting full sync for instance: {request.instance_id}")

        started_at = datetime.utcnow()

        try:
            # Create sync engine
            sync_engine = JiraSyncEngine(
                jira_client=self.jira_client,
                instance_id=request.instance_id,
            )

            # Perform sync
            stats = await sync_engine.full_sync()

            completed_at = datetime.utcnow()

            # Convert stats to DTO
            stats_dto = SyncStatsDTO(
                issues_created=stats.issues_created,
                issues_updated=stats.issues_updated,
                issues_deleted=stats.issues_deleted,
                projects_created=stats.projects_created,
                projects_updated=stats.projects_updated,
                users_created=stats.users_created,
                users_updated=stats.users_updated,
                errors=stats.errors,
                duration_seconds=stats.duration,
            )

            return FullSyncResponseDTO(
                instance_id=request.instance_id,
                started_at=started_at,
                completed_at=completed_at,
                stats=stats_dto,
                status="completed",
            )

        except Exception as e:
            logger.error(f"Full sync failed: {e}", exc_info=True)

            completed_at = datetime.utcnow()

            return FullSyncResponseDTO(
                instance_id=request.instance_id,
                started_at=started_at,
                completed_at=completed_at,
                stats=SyncStatsDTO(errors=1),
                status="failed",
                error_message=str(e),
            )


class IncrementalSyncUseCase:
    """Use case for performing incremental Jira sync."""

    def __init__(self, jira_client: JiraClient):
        """
        Initialize use case.

        Args:
            jira_client: Jira API client
        """
        self.jira_client = jira_client

    async def execute(
        self,
        request: IncrementalSyncRequestDTO,
    ) -> IncrementalSyncResponseDTO:
        """
        Perform incremental sync.

        Args:
            request: Incremental sync request

        Returns:
            Sync response with statistics
        """
        since = request.since or datetime.utcnow()

        logger.info(
            f"Starting incremental sync for instance: {request.instance_id} "
            f"since {since.isoformat()}"
        )

        started_at = datetime.utcnow()

        try:
            # Create sync engine
            sync_engine = JiraSyncEngine(
                jira_client=self.jira_client,
                instance_id=request.instance_id,
            )

            # Perform sync
            stats = await sync_engine.incremental_sync(since=since)

            completed_at = datetime.utcnow()

            # Convert stats to DTO
            stats_dto = SyncStatsDTO(
                issues_created=stats.issues_created,
                issues_updated=stats.issues_updated,
                issues_deleted=stats.issues_deleted,
                projects_created=stats.projects_created,
                projects_updated=stats.projects_updated,
                users_created=stats.users_created,
                users_updated=stats.users_updated,
                errors=stats.errors,
                duration_seconds=stats.duration,
            )

            return IncrementalSyncResponseDTO(
                instance_id=request.instance_id,
                started_at=started_at,
                completed_at=completed_at,
                since=since,
                stats=stats_dto,
                status="completed",
            )

        except Exception as e:
            logger.error(f"Incremental sync failed: {e}", exc_info=True)

            completed_at = datetime.utcnow()

            return IncrementalSyncResponseDTO(
                instance_id=request.instance_id,
                started_at=started_at,
                completed_at=completed_at,
                since=since,
                stats=SyncStatsDTO(errors=1),
                status="failed",
                error_message=str(e),
            )


class GetSyncStatusUseCase:
    """Use case for getting sync status."""

    def __init__(self):
        """Initialize use case."""
        # TODO: Add sync status repository
        pass

    async def execute(self, instance_id: UUID) -> SyncStatusDTO:
        """
        Get sync status for instance.

        Args:
            instance_id: Jira instance ID

        Returns:
            Sync status
        """
        logger.info(f"Getting sync status for instance: {instance_id}")

        # TODO: Get from sync status repository
        # For now, return mock data

        return SyncStatusDTO(
            instance_id=instance_id,
            is_syncing=False,
            last_sync_at=None,
            last_sync_status=None,
            last_sync_stats=None,
        )


__all__ = [
    "FullSyncUseCase",
    "IncrementalSyncUseCase",
    "GetSyncStatusUseCase",
]

