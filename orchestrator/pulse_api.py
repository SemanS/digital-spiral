"""API endpoints for Executive Work Pulse."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path

from . import pulse_backfill, pulse_service
from .db import session_scope
from .pulse_models import WorkItem, WorkItemMetricDaily, JiraInstance
from sqlalchemy import select, func, and_

# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/pulse", tags=["Pulse"])


# ============================================================================
# Web UI
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def pulse_dashboard_ui():
    """Serve the Pulse Dashboard HTML UI."""

    template_path = Path(__file__).parent / "templates" / "pulse_dashboard.html"
    if not template_path.exists():
        raise HTTPException(404, "Dashboard template not found")

    return template_path.read_text()


# ============================================================================
# Request/Response Models
# ============================================================================

class AddJiraInstanceRequest(BaseModel):
    base_url: str
    email: str
    api_token: str
    display_name: str


class TestJiraConnectionRequest(BaseModel):
    base_url: str
    email: str
    api_token: str


class BackfillRequest(BaseModel):
    instance_id: str
    days_back: int = 90
    max_issues: int = 1000


# ============================================================================
# Jira Instance Management
# ============================================================================

@router.post("/jira/instances")
async def add_jira_instance(request: Request, payload: AddJiraInstanceRequest):
    """Add a new Jira Cloud instance and start backfill."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    try:
        # Test connection first
        logger.info(f"Testing Jira connection for {payload.base_url}...")
        test_result = await asyncio.to_thread(
            pulse_backfill.test_jira_connection,
            payload.base_url,
            payload.email,
            payload.api_token,
        )

        if not test_result.get("success"):
            raise HTTPException(400, f"Jira connection test failed: {test_result.get('error')}")

        logger.info(f"Connection test successful. Found {test_result.get('projects_count')} projects")

        # Add instance
        instance = pulse_service.add_jira_instance(
            tenant_id=tenant_id,
            base_url=payload.base_url,
            email=payload.email,
            api_token=payload.api_token,
            display_name=payload.display_name,
        )

        logger.info(f"Jira instance added: {instance['id']}")

        # Start backfill in background
        logger.info(f"Starting backfill for instance {instance['id']}...")
        asyncio.create_task(
            asyncio.to_thread(
                pulse_backfill.backfill_jira_instance,
                instance['id'],
                90,  # days_back
                1000,  # max_issues
            )
        )

        return {
            "success": True,
            "instance": instance,
            "message": "Backfill started in background. Refresh dashboard in a few seconds."
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add Jira instance: {e}")
        raise HTTPException(500, f"Failed to add Jira instance: {e}")


@router.get("/jira/instances")
async def list_jira_instances(request: Request):
    """List all Jira instances for the tenant."""
    
    tenant_id = request.headers.get("x-tenant-id", "demo")
    
    try:
        instances = pulse_service.list_jira_instances(tenant_id)
        return {"instances": instances}
    except Exception as e:
        logger.error(f"Failed to list Jira instances: {e}")
        raise HTTPException(500, f"Failed to list Jira instances: {e}")


@router.delete("/jira/instances/{instance_id}")
async def delete_jira_instance(instance_id: str):
    """Delete a Jira instance."""
    
    try:
        success = pulse_service.delete_jira_instance(instance_id)
        if not success:
            raise HTTPException(404, "Instance not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete Jira instance: {e}")
        raise HTTPException(500, f"Failed to delete Jira instance: {e}")


@router.post("/jira/test-connection")
async def test_jira_connection(payload: TestJiraConnectionRequest):
    """Test Jira connection."""
    
    try:
        result = await asyncio.to_thread(
            pulse_backfill.test_jira_connection,
            payload.base_url,
            payload.email,
            payload.api_token,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to test Jira connection: {e}")
        return {"success": False, "error": str(e)}


@router.post("/jira/backfill")
async def backfill_jira(payload: BackfillRequest):
    """Backfill historical data from Jira."""
    
    try:
        stats = await asyncio.to_thread(
            pulse_backfill.backfill_jira_instance,
            payload.instance_id,
            payload.days_back,
            payload.max_issues,
        )
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Failed to backfill Jira: {e}")
        raise HTTPException(500, f"Failed to backfill Jira: {e}")


# ============================================================================
# Dashboard Data
# ============================================================================

@router.get("/projects")
async def get_projects(request: Request, include_archived: bool = Query(False)):
    """Get list of projects from all Jira instances."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    try:
        # Get all active Jira instances
        instances = pulse_service.list_jira_instances(tenant_id)

        all_projects = []

        for instance in instances:
            try:
                # Get instance details with API token
                inst_details = pulse_service.get_jira_instance(instance["id"])
                if not inst_details:
                    continue

                # Create adapter and fetch projects directly
                from clients.python.jira_cloud_adapter import JiraCloudAdapter
                adapter = JiraCloudAdapter(
                    inst_details["base_url"],
                    inst_details["email"],
                    inst_details["api_token"]
                )

                # Fetch all projects (including archived if requested)
                projects = await asyncio.to_thread(
                    adapter._call,
                    "GET",
                    "/rest/api/3/project",
                )

                for proj in projects:
                    # Skip archived projects unless explicitly requested
                    if proj.get("archived", False) and not include_archived:
                        logger.debug(f"Skipping archived project: {proj['key']}")
                        continue

                    all_projects.append({
                        "key": proj["key"],
                        "name": proj["name"],
                        "instance_id": instance["id"],
                        "instance_name": instance["display_name"],
                        "archived": proj.get("archived", False),
                    })

            except Exception as e:
                logger.error(f"Failed to fetch projects from {instance['display_name']}: {e}")

        return {"projects": all_projects}

    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(500, f"Failed to get projects: {e}")


@router.get("/projects/{project_key}")
async def get_project_detail(request: Request, project_key: str):
    """Get detailed information about a specific project.

    Tries each connected Jira instance. Uses the JiraCloudAdapter.search helper
    to comply with the newer Jira Cloud search endpoint. Returns 410 for
    archived projects to enable a clearer UI hint.
    """

    tenant_id = request.headers.get("x-tenant-id", "demo")

    try:
        # Get all active Jira instances
        instances = pulse_service.list_jira_instances(tenant_id)

        # Lazy import to keep module-level imports light
        from clients.python.jira_cloud_adapter import JiraCloudAdapter
        from clients.python.exceptions import JiraNotFound, JiraError

        for instance in instances:
            try:
                # Get instance details with API token
                inst_details = pulse_service.get_jira_instance(instance["id"])
                if not inst_details:
                    continue

                adapter = JiraCloudAdapter(
                    inst_details["base_url"],
                    inst_details["email"],
                    inst_details["api_token"],
                )

                # First, try to resolve the project in this instance
                try:
                    project_info = await asyncio.to_thread(adapter.get_project, project_key)
                    if project_info.get("archived"):
                        # Signal archived/deleted with 410 so UI can show a helpful tip
                        raise HTTPException(
                            status_code=410,
                            detail=(
                                f"Project {project_key} is archived in {instance['display_name']}. "
                                "Unarchive it in Jira to view details."
                            ),
                        )
                    project_name = project_info.get("name") or project_key
                except JiraNotFound:
                    # Not in this instance, try the next one
                    continue

                # Fetch issues using the adapter's search (uses /search/jql)
                result = await asyncio.to_thread(
                    adapter.search,
                    f"project = {project_key} ORDER BY updated DESC",
                    50,
                    0,
                    [
                        "summary",
                        "status",
                        "assignee",
                        "priority",
                        "issuetype",
                        "created",
                        "updated",
                    ],
                )

                issues = result.get("issues", [])

                # Calculate stats
                total = len(issues)
                open_count = len(
                    [
                        i
                        for i in issues
                        if i["fields"]["status"]["name"] not in ["Done", "Closed"]
                    ]
                )
                closed_count = total - open_count

                # Group by status
                status_counts = {}
                for issue in issues:
                    status = issue["fields"]["status"]["name"]
                    status_counts[status] = status_counts.get(status, 0) + 1

                return {
                    "project_key": project_key,
                    "project_name": project_name,
                    "instance_name": instance["display_name"],
                    "total_issues": total,
                    "open_issues": open_count,
                    "closed_issues": closed_count,
                    "status_breakdown": status_counts,
                    "issues": [
                        {
                            "key": issue["key"],
                            "summary": issue["fields"]["summary"],
                            "status": issue["fields"]["status"]["name"],
                            "priority": issue["fields"].get("priority", {}).get("name", "None"),
                            "type": issue["fields"]["issuetype"]["name"],
                            "assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned"),
                            "created": issue["fields"]["created"],
                            "updated": issue["fields"]["updated"],
                        }
                        for issue in issues
                    ],
                }

            except HTTPException:
                # Bubble up 410 archived, etc.
                raise
            except JiraError as e:
                logger.error(
                    f"Failed to fetch project {project_key} from {instance['display_name']}: {e}"
                )
                # Try next instance if Jira API said no
                continue
            except Exception as e:
                logger.error(
                    f"Unexpected error from {instance['display_name']} while fetching {project_key}: {e}"
                )
                continue

        raise HTTPException(
            404, f"Project {project_key} not found in any connected Jira instance"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project detail: {e}")
        raise HTTPException(500, f"Failed to get project detail: {e}")


@router.get("/dashboard")
async def get_dashboard(
    request: Request,
    since: Optional[str] = Query(None, description="Start date (ISO format)"),
    project_key: Optional[str] = Query(None, description="Filter by project"),
):
    """Get dashboard data for Executive Work Pulse."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    # Parse date range
    if since:
        try:
            start_date = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except Exception:
            start_date = datetime.now(UTC) - timedelta(days=7)
    else:
        start_date = datetime.now(UTC) - timedelta(days=7)

    end_date = datetime.now(UTC)
    
    try:
        with session_scope() as session:
            # Get work items for the period
            query = select(WorkItem).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.created_at >= start_date,
            )
            
            if project_key:
                query = query.where(WorkItem.project_key == project_key)
            
            work_items = session.execute(query).scalars().all()
            
            # Calculate metrics
            created_count = len([wi for wi in work_items if wi.created_at >= start_date])
            closed_count = len([wi for wi in work_items if wi.closed_at and wi.closed_at >= start_date])
            
            # WIP metrics
            wip_query = select(WorkItem).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.closed_at.is_(None),
            )
            if project_key:
                wip_query = wip_query.where(WorkItem.project_key == project_key)
            
            wip_items = session.execute(wip_query).scalars().all()
            wip_total = len(wip_items)
            wip_no_assignee = len([wi for wi in wip_items if not wi.assignee])
            wip_stuck = len([wi for wi in wip_items if wi.is_stuck])
            
            # Lead time (simplified - just closed items)
            closed_items = [wi for wi in work_items if wi.closed_at]
            lead_times = []
            for wi in closed_items:
                if wi.created_at and wi.closed_at:
                    delta = (wi.closed_at - wi.created_at).total_seconds() / 86400
                    lead_times.append(delta)
            
            lead_time_p50 = _percentile(lead_times, 0.5) if lead_times else 0
            lead_time_p90 = _percentile(lead_times, 0.9) if lead_times else 0
            
            # Get project breakdown
            projects = {}
            for wi in work_items:
                if wi.project_key:
                    if wi.project_key not in projects:
                        projects[wi.project_key] = {
                            "key": wi.project_key,
                            "created": 0,
                            "closed": 0,
                            "wip": 0,
                        }
                    if wi.created_at >= start_date:
                        projects[wi.project_key]["created"] += 1
                    if wi.closed_at and wi.closed_at >= start_date:
                        projects[wi.project_key]["closed"] += 1
                    if not wi.closed_at:
                        projects[wi.project_key]["wip"] += 1
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "throughput": {
                    "created": created_count,
                    "closed": closed_count,
                    "delta_pct": 0,  # TODO: Calculate vs 4W avg
                },
                "leadTime": {
                    "p50Days": round(lead_time_p50, 1),
                    "p90Days": round(lead_time_p90, 1),
                },
                "slaRisk": {
                    "count": 0,  # TODO: Implement SLA tracking
                    "severity": "low",
                },
                "wip": {
                    "total": wip_total,
                    "noAssignee": wip_no_assignee,
                    "stuck": wip_stuck,
                },
                "quality": {
                    "reopenRate": 0,  # TODO: Calculate reopen rate
                    "delta_pct": 0,
                },
                "projects": list(projects.values()),
                "risks": [],  # TODO: Calculate top risks
            }
    
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(500, f"Failed to get dashboard data: {e}")


@router.get("/config")
async def get_pulse_config(request: Request):
    """Get pulse configuration for the tenant."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    try:
        config = pulse_service.get_or_create_pulse_config(tenant_id)
        return config
    except Exception as e:
        logger.error(f"Failed to get pulse config: {e}")
        raise HTTPException(500, f"Failed to get pulse config: {e}")


@router.get("/debug")
async def debug_info(request: Request):
    """Debug endpoint to see database state."""

    tenant_id = request.headers.get("x-tenant-id", "demo")

    try:
        with session_scope() as session:
            # Count work items
            work_items_count = session.execute(
                select(func.count(WorkItem.id)).where(WorkItem.tenant_id == tenant_id)
            ).scalar()

            # Count by project
            projects_query = session.execute(
                select(
                    WorkItem.project_key,
                    func.count(WorkItem.id).label('count')
                ).where(
                    WorkItem.tenant_id == tenant_id
                ).group_by(WorkItem.project_key)
            )
            projects = [{"key": row[0], "count": row[1]} for row in projects_query]

            # Count Jira instances
            instances_count = session.execute(
                select(func.count(JiraInstance.id)).where(
                    JiraInstance.tenant_id == tenant_id,
                    JiraInstance.active == True
                )
            ).scalar()

            # Get sample work items
            sample_items = session.execute(
                select(WorkItem).where(
                    WorkItem.tenant_id == tenant_id
                ).limit(5)
            ).scalars().all()

            return {
                "tenant_id": tenant_id,
                "work_items_count": work_items_count,
                "jira_instances_count": instances_count,
                "projects": projects,
                "sample_items": [
                    {
                        "id": item.id,
                        "source_key": item.source_key,
                        "project_key": item.project_key,
                        "title": item.title,
                        "status": item.status,
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                    }
                    for item in sample_items
                ]
            }
    except Exception as e:
        logger.error(f"Failed to get debug info: {e}")
        raise HTTPException(500, f"Failed to get debug info: {e}")


# ============================================================================
# Helper Functions
# ============================================================================

def _percentile(values: list[float], p: float) -> float:
    """Calculate percentile of a list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * p)
    return sorted_values[min(index, len(sorted_values) - 1)]
