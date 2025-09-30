"""Data models for Executive Work Pulse - unified work item tracking across systems."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Date,
)
from sqlalchemy.orm import relationship

from .db import Base, DATABASE_URL


# Python 3.10 compatibility
try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


class JiraInstance(Base):
    """Jira Cloud instance configuration for multi-instance support."""
    
    __tablename__ = "jira_instances"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    base_url = Column(String, nullable=False)  # e.g., https://company.atlassian.net
    email = Column(String, nullable=False)  # Jira account email
    api_token_encrypted = Column(Text, nullable=False)  # Encrypted API token
    display_name = Column(String, nullable=False)  # User-friendly name
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    # Relationships
    work_items = relationship("WorkItem", back_populates="jira_instance", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("jira_inst_tenant_active", "tenant_id", "active"),
    )


class WorkItem(Base):
    """Unified work item model - superset for Jira Issue / GitHub Issue / Zendesk Ticket / PagerDuty Incident."""
    
    __tablename__ = "work_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    jira_instance_id = Column(String, ForeignKey("jira_instances.id"), nullable=True, index=True)
    
    # Source identification
    source = Column(String, nullable=False, index=True)  # jira|github|zendesk|pagerduty
    source_id = Column(String, nullable=False)  # Original ID from source system
    source_key = Column(String, nullable=True, index=True)  # e.g., SCRUM-123 for Jira
    
    # Core fields
    project_key = Column(String, nullable=True, index=True)
    title = Column(Text, nullable=False)
    type = Column(String, nullable=True)  # bug|task|incident|story|epic|...
    priority = Column(String, nullable=True)  # critical|high|medium|low
    status = Column(String, nullable=False, index=True)  # open|in_progress|done|closed|...
    
    # People
    assignee = Column(String, nullable=True, index=True)  # User ID or email
    reporter = Column(String, nullable=True)  # User ID or email
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Sprint/iteration
    sprint_id = Column(String, nullable=True, index=True)
    sprint_name = Column(String, nullable=True)
    
    # Labels and metadata
    labels = Column(JSON, nullable=True)  # JSON array for SQLite/PostgreSQL compatibility
    raw_payload = Column(JSON, nullable=True)  # Full original payload for debugging
    
    # Calculated fields (updated by aggregation jobs)
    last_transition_at = Column(DateTime(timezone=True), nullable=True)
    days_in_current_status = Column(Integer, nullable=True)
    is_stuck = Column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    jira_instance = relationship("JiraInstance", back_populates="work_items")
    transitions = relationship("WorkItemTransition", back_populates="work_item", cascade="all, delete-orphan")
    slas = relationship("WorkItemSLA", back_populates="work_item", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("wi_tenant_source_id", "tenant_id", "source", "source_id", unique=True),
        Index("wi_tenant_project_status", "tenant_id", "project_key", "status"),
        Index("wi_tenant_created", "tenant_id", "created_at"),
        Index("wi_tenant_closed", "tenant_id", "closed_at"),
        Index("wi_tenant_stuck", "tenant_id", "is_stuck"),
    )


class WorkItemTransition(Base):
    """History of status transitions for work items."""
    
    __tablename__ = "work_item_transitions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    work_item_id = Column(String, ForeignKey("work_items.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    from_status = Column(String, nullable=True)  # NULL for initial creation
    to_status = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Optional metadata
    actor = Column(String, nullable=True)  # Who made the transition
    
    # Relationships
    work_item = relationship("WorkItem", back_populates="transitions")
    
    __table_args__ = (
        Index("wit_tenant_timestamp", "tenant_id", "timestamp"),
        Index("wit_work_item_timestamp", "work_item_id", "timestamp"),
    )


class WorkItemSLA(Base):
    """SLA tracking for work items (primarily from Jira Service Management)."""
    
    __tablename__ = "work_item_slas"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    work_item_id = Column(String, ForeignKey("work_items.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    
    policy_name = Column(String, nullable=False)  # e.g., "Time to first response"
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    breached = Column(Boolean, default=False, nullable=False, index=True)
    remaining_seconds = Column(Integer, nullable=True)  # Negative if breached
    
    # Relationships
    work_item = relationship("WorkItem", back_populates="slas")
    
    __table_args__ = (
        Index("sla_tenant_due", "tenant_id", "due_at"),
        Index("sla_tenant_breached", "tenant_id", "breached"),
        Index("sla_at_risk", "tenant_id", "breached", "due_at"),  # For SLA risk queries
    )


class WorkItemMetricDaily(Base):
    """Daily aggregated metrics per project/team for fast dashboard loading."""
    
    __tablename__ = "work_item_metrics_daily"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Dimensions
    project_key = Column(String, nullable=True, index=True)
    team = Column(String, nullable=True, index=True)  # Optional team grouping
    source = Column(String, nullable=False)  # jira|github|zendesk|pagerduty
    
    # Throughput metrics
    created = Column(Integer, default=0, nullable=False)
    closed = Column(Integer, default=0, nullable=False)
    
    # WIP metrics
    wip = Column(Integer, default=0, nullable=False)  # Work in progress (not closed)
    wip_no_assignee = Column(Integer, default=0, nullable=False)
    stuck_gt_x_days = Column(Integer, default=0, nullable=False)  # Stuck > X days (configurable)
    
    # Quality metrics
    reopened = Column(Integer, default=0, nullable=False)
    
    # Lead time metrics (in days)
    lead_time_p50_days = Column(Float, nullable=True)
    lead_time_p90_days = Column(Float, nullable=True)
    lead_time_avg_days = Column(Float, nullable=True)
    
    # SLA metrics
    sla_at_risk = Column(Integer, default=0, nullable=False)  # Count of items at risk
    sla_breached = Column(Integer, default=0, nullable=False)
    
    # 4-week comparison (calculated by aggregation job)
    created_4w_avg = Column(Float, nullable=True)
    closed_4w_avg = Column(Float, nullable=True)
    created_delta_pct = Column(Float, nullable=True)  # % change vs 4w avg
    closed_delta_pct = Column(Float, nullable=True)
    
    __table_args__ = (
        Index("wimd_tenant_date", "tenant_id", "date"),
        Index("wimd_tenant_project_date", "tenant_id", "project_key", "date"),
        Index("wimd_tenant_source_date", "tenant_id", "source", "date"),
        # Unique constraint: one row per tenant/date/project/team/source
        Index("wimd_unique", "tenant_id", "date", "project_key", "team", "source", unique=True),
    )


class PulseConfig(Base):
    """Configuration for Executive Work Pulse per tenant."""
    
    __tablename__ = "pulse_configs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False, unique=True, index=True)
    
    # Configurable thresholds
    sla_risk_window_hours = Column(Integer, default=24, nullable=False)  # SLA risk if due within X hours
    stuck_threshold_days = Column(Integer, default=3, nullable=False)  # Stuck if no transition for X days
    wip_warning_threshold = Column(Integer, nullable=True)  # Warn if WIP > X
    reopen_rate_warning_pct = Column(Float, default=10.0, nullable=False)  # Warn if reopen rate > X%
    
    # Digest settings
    weekly_digest_enabled = Column(Boolean, default=True, nullable=False)
    digest_recipients = Column(JSON, nullable=True)  # JSON array of email addresses
    digest_slack_webhook = Column(String, nullable=True)
    digest_day_of_week = Column(Integer, default=1, nullable=False)  # 1=Monday
    digest_hour = Column(Integer, default=8, nullable=False)  # 8 AM
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    
    __table_args__ = (
        Index("pulse_cfg_tenant", "tenant_id"),
    )

