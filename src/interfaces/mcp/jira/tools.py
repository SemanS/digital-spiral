"""MCP Jira tool implementations."""

import time
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.audit_log_service import AuditLogService
from src.application.services.idempotency_service import IdempotencyService
from src.application.services.rate_limiter import RateLimiter
from src.infrastructure.database.models.issue import Issue
from src.infrastructure.database.models.jira_instance import JiraInstance

from .errors import NotFoundError, RateLimitError as MCPRateLimitError
from .schemas import (
    JiraAddCommentParams,
    JiraCreateIssueParams,
    JiraCreateIssueResponse,
    JiraGetIssueParams,
    JiraIssueResponse,
    JiraLinkIssuesParams,
    JiraListTransitionsParams,
    JiraSearchParams,
    JiraSearchResponse,
    JiraTransitionIssueParams,
    JiraUpdateIssueParams,
)


class MCPContext:
    """Context for MCP tool execution."""

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        rate_limiter: Optional[RateLimiter] = None,
        audit_log_service: Optional[AuditLogService] = None,
        idempotency_service: Optional[IdempotencyService] = None,
    ):
        """Initialize MCP context.

        Args:
            session: Database session
            tenant_id: Tenant ID
            user_id: User ID (optional)
            request_id: Request ID for tracing
            rate_limiter: Rate limiter service
            audit_log_service: Audit log service
            idempotency_service: Idempotency service
        """
        self.session = session
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.request_id = request_id
        self.rate_limiter = rate_limiter
        self.audit_log_service = audit_log_service or AuditLogService(session)
        self.idempotency_service = idempotency_service or IdempotencyService(session)


# Tool registry
TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str):
    """Decorator to register MCP tool.

    Args:
        name: Tool name (e.g., 'jira.search')

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        TOOL_REGISTRY[name] = func
        return func

    return decorator


async def _get_instance(
    session: AsyncSession, tenant_id: UUID, instance_id: Optional[UUID] = None
) -> JiraInstance:
    """Get Jira instance by ID or first active instance.

    Args:
        session: Database session
        tenant_id: Tenant ID
        instance_id: Instance ID (optional)

    Returns:
        JiraInstance

    Raises:
        NotFoundError: If instance not found
    """
    if instance_id:
        stmt = select(JiraInstance).where(
            JiraInstance.id == instance_id,
            JiraInstance.tenant_id == tenant_id,
            JiraInstance.is_active == True,
        )
    else:
        # Get first active instance
        stmt = select(JiraInstance).where(
            JiraInstance.tenant_id == tenant_id,
            JiraInstance.is_active == True,
        )

    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if not instance:
        raise NotFoundError(
            f"Jira instance not found",
            details={"instance_id": str(instance_id) if instance_id else None},
        )

    return instance


@register_tool("jira.search")
async def jira_search(
    params: JiraSearchParams, context: MCPContext
) -> JiraSearchResponse:
    """Search Jira issues using JQL.

    Args:
        params: Search parameters
        context: MCP context

    Returns:
        Search response with issues

    Raises:
        RateLimitError: If rate limit exceeded
        NotFoundError: If instance not found
    """
    start_time = time.time()

    # Get instance
    instance = await _get_instance(context.session, context.tenant_id, params.instance_id)

    # Rate limit check
    if context.rate_limiter:
        try:
            await context.rate_limiter.check(instance.id)
        except Exception as e:
            raise MCPRateLimitError(
                str(e), retry_after=getattr(e, "retry_after", 60)
            )

    # TODO: Implement actual Jira API call
    # For now, query from database
    stmt = select(Issue).where(
        Issue.tenant_id == context.tenant_id,
        Issue.instance_id == instance.id,
    ).limit(params.limit)

    result = await context.session.execute(stmt)
    issues = result.scalars().all()

    # Convert to dict
    issues_dict = [
        {
            "key": issue.issue_key,
            "id": issue.issue_id,
            "summary": issue.summary,
            "status": issue.status,
            "type": issue.issue_type,
            "priority": issue.priority,
        }
        for issue in issues
    ]

    query_time_ms = int((time.time() - start_time) * 1000)

    return JiraSearchResponse(
        issues=issues_dict,
        total=len(issues_dict),
        instance_id=instance.id,
        query_time_ms=query_time_ms,
    )


@register_tool("jira.get_issue")
async def jira_get_issue(
    params: JiraGetIssueParams, context: MCPContext
) -> JiraIssueResponse:
    """Get a single Jira issue by key.

    Args:
        params: Get issue parameters
        context: MCP context

    Returns:
        Issue response

    Raises:
        NotFoundError: If issue or instance not found
    """
    start_time = time.time()

    # Get instance
    instance = await _get_instance(context.session, context.tenant_id, params.instance_id)

    # Rate limit check
    if context.rate_limiter:
        try:
            await context.rate_limiter.check(instance.id)
        except Exception as e:
            raise MCPRateLimitError(
                str(e), retry_after=getattr(e, "retry_after", 60)
            )

    # Get issue
    stmt = select(Issue).where(
        Issue.tenant_id == context.tenant_id,
        Issue.instance_id == instance.id,
        Issue.issue_key == params.issue_key,
    )

    result = await context.session.execute(stmt)
    issue = result.scalar_one_or_none()

    if not issue:
        raise NotFoundError(
            f"Issue {params.issue_key} not found",
            details={"issue_key": params.issue_key},
        )

    # Convert to dict
    issue_dict = {
        "key": issue.issue_key,
        "id": issue.issue_id,
        "summary": issue.summary,
        "description": issue.description,
        "status": issue.status,
        "type": issue.issue_type,
        "priority": issue.priority,
        "assignee": issue.assignee,
        "reporter": issue.reporter,
        "created": issue.jira_created_at.isoformat() if issue.jira_created_at else None,
        "updated": issue.jira_updated_at.isoformat() if issue.jira_updated_at else None,
    }

    query_time_ms = int((time.time() - start_time) * 1000)

    return JiraIssueResponse(
        issue=issue_dict,
        instance_id=instance.id,
        query_time_ms=query_time_ms,
    )


__all__ = [
    "MCPContext",
    "TOOL_REGISTRY",
    "register_tool",
    "jira_search",
    "jira_get_issue",
]

