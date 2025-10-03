"""SQL Tools for AI Assistant - Direct database queries for fast read operations."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import Session

from .db import session_scope
from .pulse_models import WorkItem, WorkItemTransition, WorkItemMetricDaily, JiraInstance

logger = logging.getLogger(__name__)


# ============================================================================
# Predefined SQL Queries
# ============================================================================

class SQLQueryLibrary:
    """Library of predefined SQL queries for common operations."""
    
    @staticmethod
    def get_issue_comments(session: Session, issue_key: str, tenant_id: str = "demo") -> List[Dict[str, Any]]:
        """Get all comments for an issue from database.
        
        This is faster than calling Jira API for read operations.
        """
        # Note: Comments are stored in raw_payload JSON field
        stmt = select(WorkItem).where(
            and_(
                WorkItem.source_key == issue_key,
                WorkItem.tenant_id == tenant_id
            )
        )
        
        work_item = session.execute(stmt).scalar_one_or_none()
        
        if not work_item or not work_item.raw_payload:
            return []
        
        # Extract comments from raw_payload
        comments = work_item.raw_payload.get("fields", {}).get("comment", {}).get("comments", [])
        
        return [
            {
                "id": c.get("id"),
                "author": c.get("author", {}).get("displayName", "Unknown"),
                "body": c.get("body", ""),
                "created": c.get("created", "")
            }
            for c in comments
        ]
    
    @staticmethod
    def search_issues_by_project(
        session: Session,
        project_key: str,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        limit: int = 50,
        tenant_id: str = "demo"
    ) -> List[Dict[str, Any]]:
        """Search issues by project with optional filters.
        
        Much faster than Jira API for large result sets.
        """
        conditions = [
            WorkItem.project_key == project_key,
            WorkItem.tenant_id == tenant_id
        ]
        
        if status:
            conditions.append(WorkItem.status == status)
        
        if assignee:
            conditions.append(WorkItem.assignee == assignee)
        
        stmt = (
            select(WorkItem)
            .where(and_(*conditions))
            .order_by(desc(WorkItem.updated_at))
            .limit(limit)
        )
        
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                "key": item.source_key,
                "summary": item.title,
                "status": item.status,
                "assignee": item.assignee,
                "priority": item.priority,
                "type": item.type,
                "created": item.created_at.isoformat() if item.created_at else None,
                "updated": item.updated_at.isoformat() if item.updated_at else None
            }
            for item in results
        ]
    
    @staticmethod
    def get_issue_history(
        session: Session,
        issue_key: str,
        tenant_id: str = "demo"
    ) -> List[Dict[str, Any]]:
        """Get full transition history for an issue.
        
        Shows all status changes over time.
        """
        stmt = (
            select(WorkItemTransition)
            .join(WorkItem)
            .where(
                and_(
                    WorkItem.source_key == issue_key,
                    WorkItem.tenant_id == tenant_id
                )
            )
            .order_by(WorkItemTransition.transitioned_at)
        )
        
        transitions = session.execute(stmt).scalars().all()
        
        return [
            {
                "from_status": t.from_status,
                "to_status": t.to_status,
                "transitioned_at": t.transitioned_at.isoformat() if t.transitioned_at else None,
                "transitioned_by": t.transitioned_by
            }
            for t in transitions
        ]
    
    @staticmethod
    def get_project_metrics(
        session: Session,
        project_key: str,
        days: int = 30,
        tenant_id: str = "demo"
    ) -> Dict[str, Any]:
        """Get aggregated metrics for a project.
        
        Returns throughput, WIP, lead time, etc.
        """
        # Get daily metrics for last N days
        start_date = datetime.now().date() - timedelta(days=days)
        
        stmt = (
            select(WorkItemMetricDaily)
            .where(
                and_(
                    WorkItemMetricDaily.project_key == project_key,
                    WorkItemMetricDaily.tenant_id == tenant_id,
                    WorkItemMetricDaily.date >= start_date
                )
            )
            .order_by(WorkItemMetricDaily.date)
        )
        
        metrics = session.execute(stmt).scalars().all()
        
        if not metrics:
            return {
                "project_key": project_key,
                "days": days,
                "total_created": 0,
                "total_closed": 0,
                "avg_wip": 0,
                "avg_lead_time_days": 0
            }
        
        total_created = sum(m.created for m in metrics)
        total_closed = sum(m.closed for m in metrics)
        avg_wip = sum(m.wip for m in metrics) / len(metrics)
        
        # Calculate average lead time (only from metrics that have it)
        lead_times = [m.lead_time_avg_days for m in metrics if m.lead_time_avg_days is not None]
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
        
        return {
            "project_key": project_key,
            "days": days,
            "total_created": total_created,
            "total_closed": total_closed,
            "avg_wip": round(avg_wip, 1),
            "avg_lead_time_days": round(avg_lead_time, 1),
            "throughput_per_day": round(total_closed / days, 1)
        }
    
    @staticmethod
    def get_stuck_issues(
        session: Session,
        project_keys: Optional[List[str]] = None,
        days_threshold: int = 7,
        tenant_id: str = "demo"
    ) -> List[Dict[str, Any]]:
        """Get issues that are stuck (no updates for X days).

        Useful for identifying blockers.
        """
        conditions = [
            WorkItem.tenant_id == tenant_id,
            WorkItem.is_stuck == True,
            WorkItem.status.notin_(["Done", "Closed", "Resolved"])
        ]

        if project_keys:
            conditions.append(WorkItem.project_key.in_(project_keys))
        
        stmt = (
            select(WorkItem)
            .where(and_(*conditions))
            .order_by(desc(WorkItem.days_in_current_status))
            .limit(50)
        )
        
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                "key": item.source_key,
                "summary": item.title,
                "status": item.status,
                "assignee": item.assignee,
                "days_stuck": item.days_in_current_status,
                "last_updated": item.updated_at.isoformat() if item.updated_at else None
            }
            for item in results
        ]
    
    @staticmethod
    def get_user_workload(
        session: Session,
        assignee: str,
        project_keys: Optional[List[str]] = None,
        tenant_id: str = "demo"
    ) -> Dict[str, Any]:
        """Get workload summary for a user.

        Shows how many issues assigned, by status.
        """
        conditions = [
            WorkItem.tenant_id == tenant_id,
            WorkItem.assignee == assignee,
            WorkItem.status.notin_(["Done", "Closed", "Resolved"])
        ]

        if project_keys:
            conditions.append(WorkItem.project_key.in_(project_keys))
        
        stmt = select(WorkItem).where(and_(*conditions))
        
        results = session.execute(stmt).scalars().all()
        
        # Group by status
        by_status = {}
        for item in results:
            status = item.status
            if status not in by_status:
                by_status[status] = []
            by_status[status].append({
                "key": item.source_key,
                "summary": item.title,
                "priority": item.priority
            })
        
        return {
            "assignee": assignee,
            "total_open": len(results),
            "by_status": by_status
        }
    
    @staticmethod
    def search_issues_by_text(
        session: Session,
        query: str,
        project_keys: Optional[List[str]] = None,
        limit: int = 20,
        tenant_id: str = "demo"
    ) -> List[Dict[str, Any]]:
        """Full-text search in issue titles.

        Faster than Jira API for simple text searches.
        """
        conditions = [WorkItem.tenant_id == tenant_id]

        if project_keys:
            conditions.append(WorkItem.project_key.in_(project_keys))
        
        # SQLite LIKE search (case-insensitive)
        conditions.append(WorkItem.title.like(f"%{query}%"))
        
        stmt = (
            select(WorkItem)
            .where(and_(*conditions))
            .order_by(desc(WorkItem.updated_at))
            .limit(limit)
        )
        
        results = session.execute(stmt).scalars().all()
        
        return [
            {
                "key": item.source_key,
                "summary": item.title,
                "status": item.status,
                "assignee": item.assignee,
                "priority": item.priority
            }
            for item in results
        ]


# ============================================================================
# SQL Tool Executor
# ============================================================================

async def execute_sql_query(
    query_name: str,
    params: Dict[str, Any],
    tenant_id: str = "demo"
) -> Dict[str, Any]:
    """Execute a predefined SQL query.
    
    Args:
        query_name: Name of the query to execute
        params: Query parameters
        tenant_id: Tenant ID
    
    Returns:
        Query result
    """
    try:
        with session_scope() as session:
            if query_name == "get_issue_comments":
                result = SQLQueryLibrary.get_issue_comments(
                    session,
                    params["issue_key"],
                    tenant_id
                )
                return {"success": True, "result": {"comments": result, "total": len(result)}}
            
            elif query_name == "search_issues_by_project":
                result = SQLQueryLibrary.search_issues_by_project(
                    session,
                    params["project_key"],
                    params.get("status"),
                    params.get("assignee"),
                    params.get("limit", 50),
                    tenant_id
                )
                return {"success": True, "result": {"issues": result, "total": len(result)}}
            
            elif query_name == "get_issue_history":
                result = SQLQueryLibrary.get_issue_history(
                    session,
                    params["issue_key"],
                    tenant_id
                )
                return {"success": True, "result": {"history": result, "total": len(result)}}
            
            elif query_name == "get_project_metrics":
                # Support both project_keys (new) and project_key (old)
                project_keys = params.get("project_keys") or ([params["project_key"]] if params.get("project_key") else None)

                if project_keys and len(project_keys) == 1:
                    # Single project
                    result = SQLQueryLibrary.get_project_metrics(
                        session,
                        project_keys[0],
                        params.get("days", 30),
                        tenant_id
                    )
                    return {"success": True, "result": result}
                else:
                    # Multiple projects - aggregate
                    results = []
                    for pk in (project_keys or []):
                        r = SQLQueryLibrary.get_project_metrics(session, pk, params.get("days", 30), tenant_id)
                        results.append(r)

                    # Aggregate results
                    total_created = sum(r["total_created"] for r in results)
                    total_closed = sum(r["total_closed"] for r in results)
                    avg_wip = sum(r["avg_wip"] for r in results) / len(results) if results else 0
                    avg_lead_time = sum(r["avg_lead_time_days"] for r in results) / len(results) if results else 0

                    return {"success": True, "result": {
                        "project_keys": project_keys,
                        "days": params.get("days", 30),
                        "total_created": total_created,
                        "total_closed": total_closed,
                        "avg_wip": round(avg_wip, 1),
                        "avg_lead_time_days": round(avg_lead_time, 1),
                        "projects": results
                    }}

            elif query_name == "get_stuck_issues":
                # Support both project_keys (new) and project_key (old)
                project_keys = params.get("project_keys") or ([params.get("project_key")] if params.get("project_key") else None)

                result = SQLQueryLibrary.get_stuck_issues(
                    session,
                    project_keys,  # Pass list of project keys
                    params.get("days_threshold", 7),
                    tenant_id
                )
                return {"success": True, "result": {"issues": result, "total": len(result)}}

            elif query_name == "get_user_workload":
                # Support both project_keys (new) and project_key (old)
                project_keys = params.get("project_keys") or ([params.get("project_key")] if params.get("project_key") else None)

                result = SQLQueryLibrary.get_user_workload(
                    session,
                    params["assignee"],
                    project_keys,  # Pass list of project keys
                    tenant_id
                )
                return {"success": True, "result": result}

            elif query_name == "search_issues_by_text":
                # Support both project_keys (new) and project_key (old)
                project_keys = params.get("project_keys") or ([params.get("project_key")] if params.get("project_key") else None)

                result = SQLQueryLibrary.search_issues_by_text(
                    session,
                    params["query"],
                    project_keys,  # Pass list of project keys
                    params.get("limit", 20),
                    tenant_id
                )
                return {"success": True, "result": {"issues": result, "total": len(result)}}
            
            else:
                return {"success": False, "error": f"Unknown SQL query: {query_name}"}
    
    except Exception as e:
        logger.error(f"SQL query failed: {e}")
        return {"success": False, "error": str(e)}

