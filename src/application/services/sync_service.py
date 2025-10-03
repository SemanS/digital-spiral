"""Sync application service."""

from __future__ import annotations

import logging
from uuid import UUID

from src.application.dtos import (
    FullSyncRequestDTO,
    FullSyncResponseDTO,
    IncrementalSyncRequestDTO,
    IncrementalSyncResponseDTO,
    SyncStatusDTO,
)
from src.application.use_cases import (
    FullSyncUseCase,
    GetSyncStatusUseCase,
    IncrementalSyncUseCase,
)

logger = logging.getLogger(__name__)


class SyncService:
    """
    Application service for sync operations.
    
    Orchestrates sync use cases and provides high-level API for Jira synchronization.
    """

    def __init__(
        self,
        full_sync_use_case: FullSyncUseCase,
        incremental_sync_use_case: IncrementalSyncUseCase,
        get_sync_status_use_case: GetSyncStatusUseCase,
    ):
        """
        Initialize service.

        Args:
            full_sync_use_case: Full sync use case
            incremental_sync_use_case: Incremental sync use case
            get_sync_status_use_case: Get sync status use case
        """
        self.full_sync_use_case = full_sync_use_case
        self.incremental_sync_use_case = incremental_sync_use_case
        self.get_sync_status_use_case = get_sync_status_use_case

    async def full_sync(
        self,
        instance_id: UUID,
    ) -> FullSyncResponseDTO:
        """
        Perform full sync for Jira instance.

        Args:
            instance_id: Jira instance ID

        Returns:
            Sync response with statistics
        """
        logger.info(f"SyncService: Starting full sync for instance {instance_id}")

        request = FullSyncRequestDTO(instance_id=instance_id)
        return await self.full_sync_use_case.execute(request)

    async def incremental_sync(
        self,
        request: IncrementalSyncRequestDTO,
    ) -> IncrementalSyncResponseDTO:
        """
        Perform incremental sync for Jira instance.

        Args:
            request: Incremental sync request

        Returns:
            Sync response with statistics
        """
        logger.info(
            f"SyncService: Starting incremental sync for instance {request.instance_id}"
        )

        return await self.incremental_sync_use_case.execute(request)

    async def get_sync_status(
        self,
        instance_id: UUID,
    ) -> SyncStatusDTO:
        """
        Get sync status for Jira instance.

        Args:
            instance_id: Jira instance ID

        Returns:
            Sync status
        """
        logger.info(f"SyncService: Getting sync status for instance {instance_id}")

        return await self.get_sync_status_use_case.execute(instance_id)


__all__ = ["SyncService"]

