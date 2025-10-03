"""SQL query templates for MCP SQL server."""

import time
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import (
    GetIssueHistoryParams,
    GetProjectMetricsParams,
    GetUserWorkloadParams,
    LeadTimeMetricsParams,
    SQLQueryResponse,
    SearchIssuesByProjectParams,
    SearchIssuesByTextParams,
)

# Query templates registry
QUERY_TEMPLATES: Dict[str, str] = {
    "search_issues_by_project": """
        SELECT 
            id,
            issue_key as source_key,
            project_key,
            summary as title,
            issue_type as type,
            priority,
            status,
            assignee,
            reporter,
            jira_created_at as created_at,
            jira_updated_at as updated_at,
            resolved_at as closed_at
        FROM issues
        WHERE tenant_id = :tenant_id
          AND project_key = :project_key
          AND (:status IS NULL OR status = :status)
          AND (:assignee IS NULL OR assignee = :assignee)
          AND (:priority IS NULL OR priority = :priority)
        ORDER BY jira_updated_at DESC
        LIMIT :limit
    """,
    "get_project_metrics": """
        SELECT 
            date,
            created,
            closed,
            wip,
            wip_no_assignee,
            stuck_gt_x_days,
            reopened,
            lead_time_p50_days,
            lead_time_p90_days,
            lead_time_avg_days,
            sla_at_risk,
            sla_breached,
            created_4w_avg,
            closed_4w_avg,
            created_delta_pct,
            closed_delta_pct
        FROM work_item_metrics_daily
        WHERE tenant_id = :tenant_id
          AND project_key = :project_key
          AND date >= CURRENT_DATE - INTERVAL ':days days'
        ORDER BY date DESC
    """,
    "search_issues_by_text": """
        SELECT 
            id,
            issue_key as source_key,
            project_key,
            summary as title,
            issue_type as type,
            status,
            assignee,
            jira_updated_at as updated_at,
            similarity(summary, :query) as sim_score
        FROM issues
        WHERE tenant_id = :tenant_id
          AND project_key = ANY(:project_keys)
          AND summary % :query
        ORDER BY similarity(summary, :query) DESC, jira_updated_at DESC
        LIMIT :limit
    """,
    "get_issue_history": """
        SELECT 
            c.id,
            c.from_status,
            c.to_status,
            c.jira_created_at as timestamp,
            c.author_account_id as actor
        FROM changelogs c
        JOIN issues i ON c.issue_id = i.id
        WHERE i.tenant_id = :tenant_id
          AND i.issue_key = :issue_key
        ORDER BY c.jira_created_at DESC
        LIMIT :limit
    """,
    "get_user_workload": """
        SELECT 
            project_key,
            COUNT(*) as issue_count,
            COUNT(*) FILTER (WHERE priority = 'critical') as critical_count,
            COUNT(*) FILTER (WHERE priority = 'high') as high_count,
            COUNT(*) FILTER (WHERE is_stuck = true) as stuck_count,
            AVG(days_in_current_status) as avg_days_in_status
        FROM issues
        WHERE tenant_id = :tenant_id
          AND assignee = :assignee
          AND (:status IS NULL OR status = ANY(:status))
        GROUP BY project_key
        ORDER BY issue_count DESC
    """,
    "lead_time_metrics": """
        SELECT 
            date,
            project_key,
            team,
            lead_time_p50_days,
            lead_time_p90_days,
            lead_time_avg_days,
            closed as throughput
        FROM work_item_metrics_daily
        WHERE tenant_id = :tenant_id
          AND (:project_key IS NULL OR project_key = :project_key)
          AND (:team IS NULL OR team = :team)
          AND date >= CURRENT_DATE - INTERVAL ':days days'
        ORDER BY date DESC
    """,
}

# Schema mapping for each template
TEMPLATE_SCHEMAS = {
    "search_issues_by_project": SearchIssuesByProjectParams,
    "get_project_metrics": GetProjectMetricsParams,
    "search_issues_by_text": SearchIssuesByTextParams,
    "get_issue_history": GetIssueHistoryParams,
    "get_user_workload": GetUserWorkloadParams,
    "lead_time_metrics": LeadTimeMetricsParams,
}


async def execute_template(
    session: AsyncSession,
    template_name: str,
    params: Dict[str, Any],
) -> SQLQueryResponse:
    """Execute a whitelisted SQL template.

    Args:
        session: Database session
        template_name: Name of the template to execute
        params: Parameters for the template

    Returns:
        Query response with results

    Raises:
        ValueError: If template not found or validation fails
    """
    if template_name not in QUERY_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")

    # Get and validate schema
    schema_class = TEMPLATE_SCHEMAS[template_name]
    validated_params = schema_class(**params)

    # Get template
    template = QUERY_TEMPLATES[template_name]

    # Execute query
    start_time = time.time()

    result = await session.execute(
        text(template), validated_params.dict()
    )

    rows = result.fetchall()

    # Convert to list of dicts
    results = []
    if rows:
        columns = result.keys()
        results = [dict(zip(columns, row)) for row in rows]

    query_time_ms = int((time.time() - start_time) * 1000)

    return SQLQueryResponse(
        results=results,
        total=len(results),
        query_time_ms=query_time_ms,
        template_name=template_name,
    )


__all__ = [
    "QUERY_TEMPLATES",
    "TEMPLATE_SCHEMAS",
    "execute_template",
]

