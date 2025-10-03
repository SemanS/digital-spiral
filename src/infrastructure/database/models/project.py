"""Project SQLAlchemy model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin, JSONBType

if TYPE_CHECKING:
    from .issue import Issue
    from .jira_instance import JiraInstance


class Project(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Project SQLAlchemy model.

    Represents a Jira project.
    """

    __tablename__ = "projects"

    # Foreign Keys
    instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("jira_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Jira instance this project belongs to",
    )

    # Jira Identifiers
    project_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Jira project key (e.g., 'PROJ')",
    )

    project_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Jira internal project ID",
    )

    # Basic Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Project name",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Project description",
    )

    project_type: Mapped[str] = mapped_column(
        String(50),
        default="software",
        nullable=False,
        doc="Project type: software, service_desk, business",
    )

    # Configuration
    lead_account_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Project lead Jira account ID",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Project avatar URL",
    )

    url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Project URL",
    )

    # Status
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the project is archived",
    )

    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the project is private",
    )

    # Timestamps
    jira_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the project was created in Jira",
    )

    jira_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the project was last updated in Jira",
    )

    # Raw Data
    raw_jsonb: Mapped[dict] = mapped_column(
        JSONBType,
        default=dict,
        nullable=False,
        doc="Full raw Jira project JSON",
    )

    # Sync Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this project was synced",
    )

    # Relationships
    instance: Mapped[JiraInstance] = relationship(
        "JiraInstance",
        back_populates="projects",
    )

    issues: Mapped[list[Issue]] = relationship(
        "Issue",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_projects_instance_key", "instance_id", "project_key", unique=True),
        Index("ix_projects_tenant_instance", "tenant_id", "instance_id"),
        Index("ix_projects_raw_jsonb", "raw_jsonb", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Project(id={self.id}, key='{self.project_key}', name='{self.name}')>"


__all__ = ["Project"]

