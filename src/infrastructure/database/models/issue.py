"""Issue SQLAlchemy model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin, JSONBType, ArrayType

if TYPE_CHECKING:
    from .changelog import Changelog
    from .comment import Comment
    from .jira_instance import JiraInstance
    from .project import Project


class Issue(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Issue SQLAlchemy model.

    Represents a Jira issue with all its fields and relationships.
    """

    __tablename__ = "issues"

    # Foreign Keys
    instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("jira_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Jira instance this issue belongs to",
    )

    project_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Project this issue belongs to",
    )

    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Parent issue (for subtasks)",
    )

    # Jira Identifiers
    issue_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        doc="Jira issue key (e.g., 'PROJ-123')",
    )

    issue_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Jira internal issue ID",
    )

    # Basic Information
    summary: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Issue summary/title",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Issue description (plain text or ADF)",
    )

    description_format: Mapped[str] = mapped_column(
        String(20),
        default="plain",
        nullable=False,
        doc="Description format: 'plain' or 'adf'",
    )

    # Type & Status
    issue_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Issue type (Task, Bug, Story, Epic, etc.)",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Current status",
    )

    status_category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Status category (To Do, In Progress, Done)",
    )

    priority: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Issue priority",
    )

    # Assignment
    assignee_account_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Assignee Jira account ID",
    )

    reporter_account_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Reporter Jira account ID",
    )

    # Project & Parent
    project_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Project key",
    )

    parent_key: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Parent issue key (for subtasks)",
    )

    # Labels & Components
    labels: Mapped[list[str]] = mapped_column(
        ArrayType(String),
        default=list,
        nullable=False,
        doc="Issue labels",
    )

    components: Mapped[list[str]] = mapped_column(
        ArrayType(String),
        default=list,
        nullable=False,
        doc="Issue components",
    )

    # Timestamps
    jira_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the issue was created in Jira",
    )

    jira_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When the issue was last updated in Jira",
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the issue was resolved",
    )

    # Custom Fields & Raw Data
    custom_fields: Mapped[dict] = mapped_column(
        JSONBType,
        default=dict,
        nullable=False,
        doc="Custom field values (JSONB)",
    )

    raw_jsonb: Mapped[dict] = mapped_column(
        JSONBType,
        default=dict,
        nullable=False,
        doc="Full raw Jira issue JSON",
    )

    # Sync Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this issue was synced",
    )

    sync_version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
        doc="Sync version for optimistic locking",
    )

    # Relationships
    instance: Mapped[JiraInstance] = relationship(
        "JiraInstance",
        back_populates="issues",
    )

    project: Mapped[Project | None] = relationship(
        "Project",
        back_populates="issues",
    )

    parent: Mapped[Issue | None] = relationship(
        "Issue",
        remote_side="Issue.id",
        back_populates="subtasks",
    )

    subtasks: Mapped[list[Issue]] = relationship(
        "Issue",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="issue",
        cascade="all, delete-orphan",
    )

    changelogs: Mapped[list[Changelog]] = relationship(
        "Changelog",
        back_populates="issue",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_issues_instance_project", "instance_id", "project_id"),
        Index("ix_issues_instance_status", "instance_id", "status"),
        Index("ix_issues_instance_assignee", "instance_id", "assignee_account_id"),
        Index("ix_issues_instance_updated", "instance_id", "jira_updated_at"),
        Index("ix_issues_tenant_instance", "tenant_id", "instance_id"),
        Index("ix_issues_custom_fields", "custom_fields", postgresql_using="gin"),
        Index("ix_issues_raw_jsonb", "raw_jsonb", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Issue(id={self.id}, key='{self.issue_key}', summary='{self.summary[:50]}...')>"


__all__ = ["Issue"]

