"""Pydantic schemas for MCP Jira tools."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class JiraSearchParams(BaseModel):
    """Parameters for jira.search tool."""

    query: str = Field(..., min_length=1, max_length=1000, description="JQL query string")
    instance_id: Optional[UUID] = Field(
        None, description="Specific Jira instance (None = all instances)"
    )
    limit: int = Field(50, ge=1, le=100, description="Maximum results per page")
    cursor: Optional[str] = Field(None, description="Pagination cursor from previous response")
    fields: List[str] = Field(
        default=["summary", "status", "assignee", "priority"],
        max_items=50,
        description="Fields to include in response",
    )

    @validator("query")
    def validate_jql(cls, v: str) -> str:
        """Validate JQL query for forbidden keywords."""
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
        if any(word in v.upper() for word in forbidden):
            raise ValueError("Invalid JQL query: forbidden SQL keywords detected")
        return v


class JiraSearchResponse(BaseModel):
    """Response from jira.search tool."""

    issues: List[Dict[str, Any]]
    total: int
    cursor: Optional[str] = None
    instance_id: UUID
    query_time_ms: int


class JiraGetIssueParams(BaseModel):
    """Parameters for jira.get_issue tool."""

    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$", description="Issue key (e.g., PROJ-123)")
    instance_id: Optional[UUID] = Field(None, description="Auto-detect if not provided")
    expand: List[str] = Field(
        default=["changelog", "comments"],
        max_items=10,
        description="Additional data to expand",
    )


class JiraIssueResponse(BaseModel):
    """Response from jira.get_issue tool."""

    issue: Dict[str, Any]
    instance_id: UUID
    query_time_ms: int


class JiraCreateIssueParams(BaseModel):
    """Parameters for jira.create_issue tool."""

    instance_id: UUID = Field(..., description="Target Jira instance")
    project_key: str = Field(..., regex=r"^[A-Z]+$", description="Project key")
    issue_type_id: str = Field(..., description="Issue type ID (e.g., '10001')")
    summary: str = Field(..., min_length=1, max_length=255, description="Issue summary")
    description_adf: Optional[Dict[str, Any]] = Field(
        None, description="Description in ADF format"
    )
    fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Custom fields"
    )
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")

    @validator("fields")
    def validate_fields(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate custom fields count."""
        if len(v) > 50:
            raise ValueError("Maximum 50 custom fields allowed")
        return v


class JiraCreateIssueResponse(BaseModel):
    """Response from jira.create_issue tool."""

    issue: Dict[str, Any]
    instance_id: UUID
    idempotency_key: Optional[str] = None
    audit_log_id: UUID


class JiraUpdateIssueParams(BaseModel):
    """Parameters for jira.update_issue tool."""

    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    instance_id: Optional[UUID] = None
    fields: Dict[str, Any] = Field(..., min_items=1, max_items=50)
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    notify_users: bool = Field(True, description="Send notifications")


class JiraTransitionIssueParams(BaseModel):
    """Parameters for jira.transition_issue tool."""

    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    to_status: str = Field(
        ..., min_length=1, max_length=100, description="Target status name"
    )
    instance_id: Optional[UUID] = None
    comment: Optional[str] = Field(None, max_length=5000, description="Transition comment")
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    fields: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Fields to update during transition"
    )


class JiraAddCommentParams(BaseModel):
    """Parameters for jira.add_comment tool."""

    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    body_adf: Dict[str, Any] = Field(..., description="Comment body in ADF format")
    instance_id: Optional[UUID] = None
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    visibility: Optional[Dict[str, str]] = Field(
        None, description="Comment visibility restrictions"
    )

    @validator("body_adf")
    def validate_adf(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ADF format."""
        if not isinstance(v, dict):
            raise ValueError("body_adf must be a dictionary")
        if v.get("version") != 1:
            raise ValueError("ADF version must be 1")
        if v.get("type") != "doc":
            raise ValueError("ADF type must be 'doc'")
        return v


class JiraLinkIssuesParams(BaseModel):
    """Parameters for jira.link_issues tool."""

    inward_issue: str = Field(..., regex=r"^[A-Z]+-\d+$", description="Source issue")
    outward_issue: str = Field(..., regex=r"^[A-Z]+-\d+$", description="Target issue")
    link_type: str = Field(..., description="Link type (e.g., 'blocks', 'relates to')")
    instance_id: Optional[UUID] = None
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    comment: Optional[str] = Field(None, max_length=5000)


class JiraListTransitionsParams(BaseModel):
    """Parameters for jira.list_transitions tool."""

    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    instance_id: Optional[UUID] = None


__all__ = [
    "JiraSearchParams",
    "JiraSearchResponse",
    "JiraGetIssueParams",
    "JiraIssueResponse",
    "JiraCreateIssueParams",
    "JiraCreateIssueResponse",
    "JiraUpdateIssueParams",
    "JiraTransitionIssueParams",
    "JiraAddCommentParams",
    "JiraLinkIssuesParams",
    "JiraListTransitionsParams",
]

