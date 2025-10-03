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


@register_tool("jira.create_issue")
async def jira_create_issue(
    params: JiraCreateIssueParams, context: MCPContext
) -> JiraCreateIssueResponse:
    """Create a new Jira issue.

    Args:
        params: Create issue parameters
        context: MCP context

    Returns:
        Create response with issue details and audit log ID

    Raises:
        NotFoundError: If instance not found
    """
    from uuid import uuid4
    from datetime import datetime, timezone

    # Check idempotency
    if params.idempotency_key:
        is_duplicate, previous_result = await context.idempotency_service.check_and_store(
            tenant_id=context.tenant_id,
            operation="create_issue",
            key=params.idempotency_key,
        )
        if is_duplicate and previous_result:
            return JiraCreateIssueResponse(**previous_result)

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

    # TODO: Implement actual Jira API call to create issue
    # For now, create in database
    new_issue = Issue(
        id=uuid4(),
        tenant_id=context.tenant_id,
        instance_id=instance.id,
        issue_key=f"{params.project_key}-{uuid4().hex[:4].upper()}",  # Temporary
        issue_id=str(uuid4()),
        summary=params.summary,
        description=params.description_adf.get("content", "") if params.description_adf else None,
        issue_type=params.issue_type_id,
        status="Open",
        priority="Medium",
        custom_fields=params.fields or {},
        raw_jsonb={},
        jira_created_at=datetime.now(timezone.utc),
        jira_updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    context.session.add(new_issue)
    await context.session.flush()

    # Create audit log
    audit_log = await context.audit_log_service.log_create(
        tenant_id=context.tenant_id,
        resource_type="issue",
        resource_id=new_issue.issue_key,
        data={
            "summary": params.summary,
            "project_key": params.project_key,
            "issue_type": params.issue_type_id,
        },
        user_id=context.user_id,
        request_id=context.request_id,
        metadata={"instance_id": str(instance.id)},
    )

    # Convert to response
    issue_dict = {
        "key": new_issue.issue_key,
        "id": new_issue.issue_id,
        "summary": new_issue.summary,
        "status": new_issue.status,
        "type": new_issue.issue_type,
    }

    response = JiraCreateIssueResponse(
        issue=issue_dict,
        instance_id=instance.id,
        idempotency_key=params.idempotency_key,
        audit_log_id=audit_log.id,
    )

    # Store idempotency result
    if params.idempotency_key:
        await context.idempotency_service.store(
            tenant_id=context.tenant_id,
            operation="create_issue",
            key=params.idempotency_key,
            result=response.dict(),
            request_id=context.request_id,
        )

    return response


@register_tool("jira.update_issue")
async def jira_update_issue(
    params: JiraUpdateIssueParams, context: MCPContext
) -> Dict[str, Any]:
    """Update a Jira issue.

    Args:
        params: Update issue parameters
        context: MCP context

    Returns:
        Update response

    Raises:
        NotFoundError: If issue or instance not found
    """
    # Check idempotency
    if params.idempotency_key:
        is_duplicate, previous_result = await context.idempotency_service.check_and_store(
            tenant_id=context.tenant_id,
            operation="update_issue",
            key=params.idempotency_key,
        )
        if is_duplicate and previous_result:
            return previous_result

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

    # Store before state
    before = {
        "summary": issue.summary,
        "description": issue.description,
        "status": issue.status,
        "priority": issue.priority,
    }

    # Update fields
    for field, value in params.fields.items():
        if hasattr(issue, field):
            setattr(issue, field, value)

    from datetime import datetime, timezone
    issue.updated_at = datetime.now(timezone.utc)
    issue.jira_updated_at = datetime.now(timezone.utc)

    await context.session.flush()

    # Store after state
    after = {
        "summary": issue.summary,
        "description": issue.description,
        "status": issue.status,
        "priority": issue.priority,
    }

    # Create audit log
    await context.audit_log_service.log_update(
        tenant_id=context.tenant_id,
        resource_type="issue",
        resource_id=issue.issue_key,
        before=before,
        after=after,
        user_id=context.user_id,
        request_id=context.request_id,
        metadata={"instance_id": str(instance.id)},
    )

    response = {
        "success": True,
        "issue_key": issue.issue_key,
        "updated_fields": list(params.fields.keys()),
    }

    # Store idempotency result
    if params.idempotency_key:
        await context.idempotency_service.store(
            tenant_id=context.tenant_id,
            operation="update_issue",
            key=params.idempotency_key,
            result=response,
            request_id=context.request_id,
        )

    return response


@register_tool("jira.transition_issue")
async def jira_transition_issue(
    params: JiraTransitionIssueParams, context: MCPContext
) -> Dict[str, Any]:
    """Transition a Jira issue to a new status.

    Args:
        params: Transition issue parameters
        context: MCP context

    Returns:
        Transition response

    Raises:
        NotFoundError: If issue or instance not found
    """
    # Check idempotency
    if params.idempotency_key:
        is_duplicate, previous_result = await context.idempotency_service.check_and_store(
            tenant_id=context.tenant_id,
            operation="transition_issue",
            key=params.idempotency_key,
        )
        if is_duplicate and previous_result:
            return previous_result

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

    # Store old status
    old_status = issue.status

    # Update status
    issue.status = params.to_status
    from datetime import datetime, timezone
    issue.updated_at = datetime.now(timezone.utc)
    issue.jira_updated_at = datetime.now(timezone.utc)

    await context.session.flush()

    # Create audit log
    await context.audit_log_service.log(
        tenant_id=context.tenant_id,
        action="transition",
        resource_type="issue",
        resource_id=issue.issue_key,
        changes={
            "before": {"status": old_status},
            "after": {"status": params.to_status},
        },
        user_id=context.user_id,
        request_id=context.request_id,
        metadata={
            "instance_id": str(instance.id),
            "comment": params.comment,
        },
    )

    response = {
        "success": True,
        "issue_key": issue.issue_key,
        "from_status": old_status,
        "to_status": params.to_status,
    }

    # Store idempotency result
    if params.idempotency_key:
        await context.idempotency_service.store(
            tenant_id=context.tenant_id,
            operation="transition_issue",
            key=params.idempotency_key,
            result=response,
            request_id=context.request_id,
        )

    return response


@register_tool("jira.add_comment")
async def jira_add_comment(
    params: JiraAddCommentParams, context: MCPContext
) -> Dict[str, Any]:
    """Add a comment to a Jira issue.

    Args:
        params: Add comment parameters
        context: MCP context

    Returns:
        Comment response

    Raises:
        NotFoundError: If issue or instance not found
    """
    from src.infrastructure.database.models.comment import Comment
    from uuid import uuid4
    from datetime import datetime, timezone

    # Check idempotency
    if params.idempotency_key:
        is_duplicate, previous_result = await context.idempotency_service.check_and_store(
            tenant_id=context.tenant_id,
            operation="add_comment",
            key=params.idempotency_key,
        )
        if is_duplicate and previous_result:
            return previous_result

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

    # Create comment
    comment = Comment(
        id=uuid4(),
        tenant_id=context.tenant_id,
        issue_id=issue.id,
        comment_id=str(uuid4()),
        author_account_id=context.user_id or "unknown",
        body=str(params.body_adf),  # TODO: Store ADF properly
        jira_created_at=datetime.now(timezone.utc),
        jira_updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    context.session.add(comment)
    await context.session.flush()

    # Create audit log
    await context.audit_log_service.log(
        tenant_id=context.tenant_id,
        action="add_comment",
        resource_type="issue",
        resource_id=issue.issue_key,
        changes={
            "before": None,
            "after": {"comment_id": comment.comment_id, "author": context.user_id},
        },
        user_id=context.user_id,
        request_id=context.request_id,
        metadata={"instance_id": str(instance.id)},
    )

    response = {
        "success": True,
        "issue_key": issue.issue_key,
        "comment_id": comment.comment_id,
    }

    # Store idempotency result
    if params.idempotency_key:
        await context.idempotency_service.store(
            tenant_id=context.tenant_id,
            operation="add_comment",
            key=params.idempotency_key,
            result=response,
            request_id=context.request_id,
        )

    return response


@register_tool("jira.link_issues")
async def jira_link_issues(
    params: JiraLinkIssuesParams, context: MCPContext
) -> Dict[str, Any]:
    """Link two Jira issues.

    Args:
        params: Link issues parameters
        context: MCP context

    Returns:
        Link response

    Raises:
        NotFoundError: If issues or instance not found
    """
    # Check idempotency
    if params.idempotency_key:
        is_duplicate, previous_result = await context.idempotency_service.check_and_store(
            tenant_id=context.tenant_id,
            operation="link_issues",
            key=params.idempotency_key,
        )
        if is_duplicate and previous_result:
            return previous_result

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

    # Get both issues
    stmt = select(Issue).where(
        Issue.tenant_id == context.tenant_id,
        Issue.instance_id == instance.id,
        Issue.issue_key.in_([params.inward_issue, params.outward_issue]),
    )

    result = await context.session.execute(stmt)
    issues = result.scalars().all()

    if len(issues) != 2:
        raise NotFoundError(
            f"One or both issues not found",
            details={
                "inward_issue": params.inward_issue,
                "outward_issue": params.outward_issue,
            },
        )

    # TODO: Store link in database (need to create IssueLink model)
    # For now, just log the action

    # Create audit log
    await context.audit_log_service.log(
        tenant_id=context.tenant_id,
        action="link_issues",
        resource_type="issue",
        resource_id=params.inward_issue,
        changes={
            "before": None,
            "after": {
                "link_type": params.link_type,
                "outward_issue": params.outward_issue,
            },
        },
        user_id=context.user_id,
        request_id=context.request_id,
        metadata={"instance_id": str(instance.id)},
    )

    response = {
        "success": True,
        "inward_issue": params.inward_issue,
        "outward_issue": params.outward_issue,
        "link_type": params.link_type,
    }

    # Store idempotency result
    if params.idempotency_key:
        await context.idempotency_service.store(
            tenant_id=context.tenant_id,
            operation="link_issues",
            key=params.idempotency_key,
            result=response,
            request_id=context.request_id,
        )

    return response


@register_tool("jira.list_transitions")
async def jira_list_transitions(
    params: JiraListTransitionsParams, context: MCPContext
) -> Dict[str, Any]:
    """List available transitions for a Jira issue.

    Args:
        params: List transitions parameters
        context: MCP context

    Returns:
        List of available transitions

    Raises:
        NotFoundError: If issue or instance not found
    """
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

    # TODO: Get actual transitions from Jira API
    # For now, return common transitions based on current status
    transitions = []
    current_status = issue.status

    if current_status == "Open":
        transitions = [
            {"id": "11", "name": "In Progress", "to": "In Progress"},
            {"id": "21", "name": "Done", "to": "Done"},
        ]
    elif current_status == "In Progress":
        transitions = [
            {"id": "31", "name": "Done", "to": "Done"},
            {"id": "41", "name": "Blocked", "to": "Blocked"},
        ]
    elif current_status == "Done":
        transitions = [
            {"id": "51", "name": "Reopen", "to": "Open"},
        ]

    return {
        "issue_key": issue.issue_key,
        "current_status": current_status,
        "transitions": transitions,
    }


__all__ = [
    "MCPContext",
    "TOOL_REGISTRY",
    "register_tool",
    "jira_search",
    "jira_get_issue",
    "jira_create_issue",
    "jira_update_issue",
    "jira_transition_issue",
    "jira_add_comment",
    "jira_link_issues",
    "jira_list_transitions",
]

