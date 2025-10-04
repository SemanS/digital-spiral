"""Analytics Job model for job orchestration."""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin, TimestampMixin, TenantMixin


class JobType(str, Enum):
    """Analytics job types."""
    NL_QUERY = "nl_query"  # Natural language query
    SPEC_QUERY = "spec_query"  # Direct AnalyticsSpec query
    METRIC_QUERY = "metric_query"  # Predefined metric query


class JobStatus(str, Enum):
    """Analytics job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalyticsJob(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """Analytics job for tracking query execution.
    
    Tracks the lifecycle of analytics queries from submission
    to completion, including NL translation, SQL generation,
    and result caching.
    """
    
    __tablename__ = "analytics_jobs"
    
    # User Information
    user_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User who submitted the job"
    )
    
    # Job Configuration
    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Job type: nl_query, spec_query, or metric_query"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Job status: pending, running, completed, failed, cancelled"
    )
    
    # Input Data
    input_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Input data (NL query, AnalyticsSpec, or metric name + params)"
    )
    
    # Processing Results
    spec: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Generated or provided AnalyticsSpec"
    )
    
    sql_query: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Generated SQL query"
    )
    
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Query results and metadata"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if job failed"
    )
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When job execution started"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When job execution completed"
    )
    
    # Table arguments
    __table_args__ = (
        Index("idx_analytics_jobs_tenant_user", "tenant_id", "user_id"),
        Index("idx_analytics_jobs_status", "status"),
        Index("idx_analytics_jobs_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of AnalyticsJob."""
        return (
            f"<AnalyticsJob(id={self.id}, type='{self.job_type}', "
            f"status='{self.status}', user_id='{self.user_id}')>"
        )
    
    @property
    def is_pending(self) -> bool:
        """Check if job is pending."""
        return self.status == JobStatus.PENDING.value
    
    @property
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == JobStatus.RUNNING.value
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status == JobStatus.COMPLETED.value
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == JobStatus.FAILED.value
    
    @property
    def is_finished(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in [
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
        ]
    
    @property
    def execution_time_seconds(self) -> Optional[float]:
        """Calculate job execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def natural_language_query(self) -> Optional[str]:
        """Get natural language query if job type is nl_query."""
        if self.job_type == JobType.NL_QUERY.value:
            return self.input_data.get("query")
        return None
    
    @property
    def metric_name(self) -> Optional[str]:
        """Get metric name if job type is metric_query."""
        if self.job_type == JobType.METRIC_QUERY.value:
            return self.input_data.get("metric_name")
        return None
    
    def mark_as_running(self) -> None:
        """Mark job as running."""
        self.status = JobStatus.RUNNING.value
        self.started_at = datetime.utcnow()
    
    def mark_as_completed(self, result_data: Dict[str, Any]) -> None:
        """Mark job as completed with results."""
        self.status = JobStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.result_data = result_data
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark job as failed with error message."""
        self.status = JobStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def mark_as_cancelled(self) -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED.value
        self.completed_at = datetime.utcnow()

