"""Sync REST API endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dtos import (
    FullSyncResponseDTO,
    IncrementalSyncRequestDTO,
    IncrementalSyncResponseDTO,
    SyncStatusDTO,
)
from src.application.services import SyncService
from src.interfaces.rest.dependencies import get_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/full/{instance_id}", response_model=FullSyncResponseDTO)
async def full_sync(
    instance_id: UUID,
    service: SyncService = Depends(get_sync_service),
):
    """
    Perform full sync for Jira instance.

    Args:
        instance_id: Jira instance ID
        service: Sync service

    Returns:
        Sync response with statistics
    """
    logger.info(f"POST /sync/full/{instance_id}")

    try:
        return await service.full_sync(instance_id)
    except Exception as e:
        logger.error(f"Full sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Full sync failed: {str(e)}",
        )


@router.post("/incremental", response_model=IncrementalSyncResponseDTO)
async def incremental_sync(
    sync_request: IncrementalSyncRequestDTO,
    service: SyncService = Depends(get_sync_service),
):
    """
    Perform incremental sync for Jira instance.

    Args:
        sync_request: Incremental sync request
        service: Sync service

    Returns:
        Sync response with statistics
    """
    logger.info(f"POST /sync/incremental - {sync_request.instance_id}")

    try:
        return await service.incremental_sync(sync_request)
    except Exception as e:
        logger.error(f"Incremental sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Incremental sync failed: {str(e)}",
        )


@router.get("/status/{instance_id}", response_model=SyncStatusDTO)
async def get_sync_status(
    instance_id: UUID,
    service: SyncService = Depends(get_sync_service),
):
    """
    Get sync status for Jira instance.

    Args:
        instance_id: Jira instance ID
        service: Sync service

    Returns:
        Sync status
    """
    logger.info(f"GET /sync/status/{instance_id}")

    return await service.get_sync_status(instance_id)


__all__ = ["router"]

