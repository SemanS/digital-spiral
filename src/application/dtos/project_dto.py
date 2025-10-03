"""Project Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectDTO(BaseModel):
    """Project DTO for API responses."""

    id: UUID
    instance_id: UUID
    project_key: str
    project_id: str
    name: str
    description: str | None = None
    project_type: str
    lead_account_id: str | None = None
    avatar_url: str | None = None
    url: str | None = None
    is_archived: bool = False
    is_private: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ProjectListResponseDTO(BaseModel):
    """DTO for paginated project list response."""

    items: list[ProjectDTO]
    total: int
    skip: int
    limit: int
    has_more: bool


class ProjectSyncRequestDTO(BaseModel):
    """DTO for project sync request."""

    instance_id: UUID
    project_key: str


class ProjectSyncResponseDTO(BaseModel):
    """DTO for project sync response."""

    project: ProjectDTO
    synced_at: datetime
    issues_synced: int = 0


__all__ = [
    "ProjectDTO",
    "ProjectListResponseDTO",
    "ProjectSyncRequestDTO",
    "ProjectSyncResponseDTO",
]

