"""Service layer for Executive Work Pulse - Jira connector and data ingestion."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import session_scope
from .pulse_models import JiraInstance, WorkItem, WorkItemTransition, PulseConfig

# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

logger = logging.getLogger(__name__)


# ============================================================================
# Jira Instance Management
# ============================================================================

def add_jira_instance(
    tenant_id: str,
    base_url: str,
    email: str,
    api_token: str,
    display_name: str,
) -> dict[str, Any]:
    """Add a new Jira Cloud instance for a tenant."""

    base_url = base_url.rstrip("/")

    with session_scope() as session:
        # Check if instance already exists (same base_url + email)
        stmt = select(JiraInstance).where(
            JiraInstance.tenant_id == tenant_id,
            JiraInstance.base_url == base_url,
            JiraInstance.email == email,
            JiraInstance.active == True,
        )
        existing = session.execute(stmt).scalar_one_or_none()

        if existing:
            raise ValueError(
                f"Jira instance already exists: {display_name} ({base_url})"
            )

        # Simple encryption (in production use proper encryption like Fernet)
        api_token_encrypted = _encrypt_token(api_token)

        instance = JiraInstance(
            tenant_id=tenant_id,
            base_url=base_url,
            email=email,
            api_token_encrypted=api_token_encrypted,
            display_name=display_name,
            active=True,
        )
        session.add(instance)
        session.flush()

        return {
            "id": instance.id,
            "tenant_id": instance.tenant_id,
            "base_url": instance.base_url,
            "email": instance.email,
            "display_name": instance.display_name,
            "active": instance.active,
            "created_at": instance.created_at.isoformat(),
        }


def list_jira_instances(tenant_id: str) -> list[dict[str, Any]]:
    """List all Jira instances for a tenant."""
    
    with session_scope() as session:
        stmt = select(JiraInstance).where(
            JiraInstance.tenant_id == tenant_id,
            JiraInstance.active == True,
        )
        instances = session.execute(stmt).scalars().all()
        
        return [
            {
                "id": inst.id,
                "tenant_id": inst.tenant_id,
                "base_url": inst.base_url,
                "email": inst.email,
                "display_name": inst.display_name,
                "active": inst.active,
                "created_at": inst.created_at.isoformat(),
            }
            for inst in instances
        ]


def get_jira_instance(instance_id: str) -> Optional[dict[str, Any]]:
    """Get a specific Jira instance."""
    
    with session_scope() as session:
        instance = session.get(JiraInstance, instance_id)
        if not instance:
            return None
        
        return {
            "id": instance.id,
            "tenant_id": instance.tenant_id,
            "base_url": instance.base_url,
            "email": instance.email,
            "display_name": instance.display_name,
            "active": instance.active,
            "api_token": _decrypt_token(instance.api_token_encrypted),
        }


def delete_jira_instance(instance_id: str) -> bool:
    """Soft delete a Jira instance."""
    
    with session_scope() as session:
        instance = session.get(JiraInstance, instance_id)
        if not instance:
            return False
        
        instance.active = False
        session.flush()
        return True


# ============================================================================
# Work Item Ingestion
# ============================================================================

def upsert_work_item_from_jira(
    tenant_id: str,
    jira_instance_id: str,
    issue_data: dict[str, Any],
) -> str:
    """Upsert a work item from Jira issue data."""
    
    fields = issue_data.get("fields", {})
    key = issue_data.get("key")
    issue_id = issue_data.get("id")
    
    # Extract fields
    project = fields.get("project", {})
    project_key = project.get("key")
    
    issuetype = fields.get("issuetype", {})
    issue_type = issuetype.get("name", "").lower()
    
    priority = fields.get("priority", {})
    priority_name = priority.get("name", "medium").lower()
    
    status = fields.get("status", {})
    status_name = status.get("name", "open")
    
    assignee = fields.get("assignee", {})
    assignee_id = assignee.get("accountId") if assignee else None
    
    reporter = fields.get("reporter", {})
    reporter_id = reporter.get("accountId") if reporter else None
    
    # Timestamps
    created_str = fields.get("created")
    updated_str = fields.get("updated")
    resolution_date_str = fields.get("resolutiondate")
    
    created_at = _parse_datetime(created_str) if created_str else datetime.now(UTC)
    updated_at = _parse_datetime(updated_str) if updated_str else datetime.now(UTC)
    closed_at = _parse_datetime(resolution_date_str) if resolution_date_str else None
    
    # Sprint
    sprint_field = fields.get("sprint")
    sprint_id = None
    sprint_name = None
    if sprint_field:
        if isinstance(sprint_field, dict):
            sprint_id = str(sprint_field.get("id", ""))
            sprint_name = sprint_field.get("name")
        elif isinstance(sprint_field, list) and sprint_field:
            sprint_id = str(sprint_field[0].get("id", ""))
            sprint_name = sprint_field[0].get("name")
    
    # Labels
    labels = fields.get("labels", [])
    
    with session_scope() as session:
        # Check if work item exists
        stmt = select(WorkItem).where(
            WorkItem.tenant_id == tenant_id,
            WorkItem.source == "jira",
            WorkItem.source_id == issue_id,
        )
        work_item = session.execute(stmt).scalar_one_or_none()
        
        if work_item:
            # Update existing
            old_status = work_item.status
            work_item.title = fields.get("summary", "")
            work_item.type = issue_type
            work_item.priority = priority_name
            work_item.status = status_name
            work_item.assignee = assignee_id
            work_item.reporter = reporter_id
            work_item.updated_at = updated_at
            work_item.closed_at = closed_at
            work_item.sprint_id = sprint_id
            work_item.sprint_name = sprint_name
            work_item.labels = labels
            work_item.raw_payload = issue_data
            
            # Record transition if status changed
            if old_status != status_name:
                transition = WorkItemTransition(
                    work_item_id=work_item.id,
                    tenant_id=tenant_id,
                    from_status=old_status,
                    to_status=status_name,
                    timestamp=updated_at,
                )
                session.add(transition)
                work_item.last_transition_at = updated_at
        else:
            # Create new
            work_item = WorkItem(
                tenant_id=tenant_id,
                jira_instance_id=jira_instance_id,
                source="jira",
                source_id=issue_id,
                source_key=key,
                project_key=project_key,
                title=fields.get("summary", ""),
                type=issue_type,
                priority=priority_name,
                status=status_name,
                assignee=assignee_id,
                reporter=reporter_id,
                created_at=created_at,
                updated_at=updated_at,
                closed_at=closed_at,
                sprint_id=sprint_id,
                sprint_name=sprint_name,
                labels=labels,
                raw_payload=issue_data,
                last_transition_at=created_at,
            )
            session.add(work_item)
            session.flush()
            
            # Record initial transition
            transition = WorkItemTransition(
                work_item_id=work_item.id,
                tenant_id=tenant_id,
                from_status=None,
                to_status=status_name,
                timestamp=created_at,
            )
            session.add(transition)
        
        session.flush()
        return work_item.id


# ============================================================================
# Pulse Configuration
# ============================================================================

def get_or_create_pulse_config(tenant_id: str) -> dict[str, Any]:
    """Get or create pulse configuration for a tenant."""
    
    with session_scope() as session:
        stmt = select(PulseConfig).where(PulseConfig.tenant_id == tenant_id)
        config = session.execute(stmt).scalar_one_or_none()
        
        if not config:
            config = PulseConfig(tenant_id=tenant_id)
            session.add(config)
            session.flush()
        
        return {
            "tenant_id": config.tenant_id,
            "sla_risk_window_hours": config.sla_risk_window_hours,
            "stuck_threshold_days": config.stuck_threshold_days,
            "wip_warning_threshold": config.wip_warning_threshold,
            "reopen_rate_warning_pct": config.reopen_rate_warning_pct,
            "weekly_digest_enabled": config.weekly_digest_enabled,
        }


# ============================================================================
# Helper Functions
# ============================================================================

def _encrypt_token(token: str) -> str:
    """Simple encryption (use proper encryption in production)."""
    # For MVP, just hash it (in production use Fernet or similar)
    return hashlib.sha256(token.encode()).hexdigest() + ":" + token


def _decrypt_token(encrypted: str) -> str:
    """Simple decryption (use proper encryption in production)."""
    if ":" in encrypted:
        return encrypted.split(":", 1)[1]
    return encrypted


def _parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string."""
    try:
        # Remove timezone suffix and parse
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)
    except Exception:
        return datetime.now(UTC)

