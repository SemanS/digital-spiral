"""Issue Data Transfer Objects."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class IssueDTO(BaseModel):
    """Issue DTO for API responses."""

    id: UUID
    instance_id: UUID
    issue_key: str
    issue_id: str
    summary: str
    description: str | None = None
    issue_type: str
    status: str
    priority: str
    assignee_account_id: str | None = None
    reporter_account_id: str | None = None
    project_key: str
    parent_key: str | None = None
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class IssueCreateDTO(BaseModel):
    """DTO for creating an issue."""

    instance_id: UUID
    project_key: str
    summary: str
    description: str | None = None
    issue_type: str = "Task"
    priority: str = "Medium"
    assignee_account_id: str | None = None
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class IssueUpdateDTO(BaseModel):
    """DTO for updating an issue."""

    summary: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee_account_id: str | None = None
    labels: list[str] | None = None
    components: list[str] | None = None
    custom_fields: dict[str, Any] | None = None


class IssueSearchDTO(BaseModel):
    """DTO for searching issues."""

    instance_id: UUID
    project_key: str | None = None
    status: str | None = None
    assignee_account_id: str | None = None
    issue_type: str | None = None
    priority: str | None = None
    labels: list[str] | None = None
    query: str | None = None
    skip: int = 0
    limit: int = 50


class IssueListResponseDTO(BaseModel):
    """DTO for paginated issue list response."""

    items: list[IssueDTO]
    total: int
    skip: int
    limit: int
    has_more: bool


class IssueSyncRequestDTO(BaseModel):
    """DTO for issue sync request."""

    instance_id: UUID
    issue_key: str


class IssueSyncResponseDTO(BaseModel):
    """DTO for issue sync response."""

    issue: IssueDTO
    synced_at: datetime
    comments_synced: int = 0
    changelogs_synced: int = 0


__all__ = [
    "IssueDTO",
    "IssueCreateDTO",
    "IssueUpdateDTO",
    "IssueSearchDTO",
    "IssueListResponseDTO",
    "IssueSyncRequestDTO",
    "IssueSyncResponseDTO",
]

