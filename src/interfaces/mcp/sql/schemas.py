"""Pydantic schemas for MCP SQL query templates."""

import re
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class SearchIssuesByProjectParams(BaseModel):
    """Parameters for search_issues_by_project template."""

    project_key: str = Field(..., regex=r"^[A-Z0-9-]+$", max_length=50)
    status: Optional[str] = Field(None, max_length=100)
    assignee: Optional[str] = Field(None, max_length=255)
    priority: Optional[str] = Field(None, max_length=50)
    limit: int = Field(50, ge=1, le=100)
    tenant_id: str = Field(..., description="Tenant ID from auth context")


class GetProjectMetricsParams(BaseModel):
    """Parameters for get_project_metrics template."""

    project_key: str = Field(..., regex=r"^[A-Z0-9-]+$", max_length=50)
    days: int = Field(30, ge=1, le=365, description="Number of days to look back")
    tenant_id: str = Field(...)


class SearchIssuesByTextParams(BaseModel):
    """Parameters for search_issues_by_text template."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    project_keys: List[str] = Field(
        ..., min_items=1, max_items=50, description="Projects to search"
    )
    limit: int = Field(20, ge=1, le=100)
    tenant_id: str = Field(...)

    @validator("project_keys")
    def validate_project_keys(cls, v: List[str]) -> List[str]:
        """Validate project keys format."""
        for key in v:
            if not re.match(r"^[A-Z0-9-]+$", key):
                raise ValueError(f"Invalid project key: {key}")
        return v


class GetIssueHistoryParams(BaseModel):
    """Parameters for get_issue_history template."""

    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    tenant_id: str = Field(...)
    limit: int = Field(100, ge=1, le=500)


class GetUserWorkloadParams(BaseModel):
    """Parameters for get_user_workload template."""

    assignee: str = Field(..., max_length=255)
    status: Optional[List[str]] = Field(None, max_items=20)
    tenant_id: str = Field(...)


class LeadTimeMetricsParams(BaseModel):
    """Parameters for lead_time_metrics template."""

    project_key: Optional[str] = Field(None, regex=r"^[A-Z0-9-]+$")
    team: Optional[str] = Field(None, max_length=100)
    days: int = Field(30, ge=1, le=365)
    tenant_id: str = Field(...)


class SQLQueryResponse(BaseModel):
    """Response from SQL query execution."""

    results: List[dict]
    total: int
    query_time_ms: int
    template_name: str


__all__ = [
    "SearchIssuesByProjectParams",
    "GetProjectMetricsParams",
    "SearchIssuesByTextParams",
    "GetIssueHistoryParams",
    "GetUserWorkloadParams",
    "LeadTimeMetricsParams",
    "SQLQueryResponse",
]

