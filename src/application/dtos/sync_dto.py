"""Sync Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SyncStatsDTO(BaseModel):
    """DTO for sync statistics."""

    issues_created: int = 0
    issues_updated: int = 0
    issues_deleted: int = 0
    projects_created: int = 0
    projects_updated: int = 0
    users_created: int = 0
    users_updated: int = 0
    errors: int = 0
    duration_seconds: float | None = None


class FullSyncRequestDTO(BaseModel):
    """DTO for full sync request."""

    instance_id: UUID


class FullSyncResponseDTO(BaseModel):
    """DTO for full sync response."""

    instance_id: UUID
    started_at: datetime
    completed_at: datetime
    stats: SyncStatsDTO
    status: str = "completed"
    error_message: str | None = None


class IncrementalSyncRequestDTO(BaseModel):
    """DTO for incremental sync request."""

    instance_id: UUID
    since: datetime | None = None


class IncrementalSyncResponseDTO(BaseModel):
    """DTO for incremental sync response."""

    instance_id: UUID
    started_at: datetime
    completed_at: datetime
    since: datetime
    stats: SyncStatsDTO
    status: str = "completed"
    error_message: str | None = None


class SyncStatusDTO(BaseModel):
    """DTO for sync status."""

    instance_id: UUID
    is_syncing: bool
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    last_sync_stats: SyncStatsDTO | None = None


__all__ = [
    "SyncStatsDTO",
    "FullSyncRequestDTO",
    "FullSyncResponseDTO",
    "IncrementalSyncRequestDTO",
    "IncrementalSyncResponseDTO",
    "SyncStatusDTO",
]

