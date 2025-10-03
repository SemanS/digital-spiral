"""Changelog SQLAlchemy model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .issue import Issue
    from .jira_instance import JiraInstance


class Changelog(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Changelog SQLAlchemy model.

    Represents a Jira issue change history entry.
    """

    __tablename__ = "changelogs"

    # Foreign Keys
    instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("jira_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Jira instance this changelog belongs to",
    )

    issue_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Issue this changelog belongs to",
    )

    # Jira Identifiers
    changelog_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Jira internal changelog ID",
    )

    issue_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Issue key for quick lookup",
    )

    # Author
    author_account_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Author Jira account ID",
    )

    # Changes (stored as JSONB array)
    items: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Array of change items (field, from, to)",
    )

    # Timestamp
    jira_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="When the change was made in Jira",
    )

    # Raw Data
    raw_jsonb: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="Full raw Jira changelog JSON",
    )

    # Sync Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this changelog was synced",
    )

    # Relationships
    instance: Mapped[JiraInstance] = relationship(
        "JiraInstance",
        back_populates="changelogs",
    )

    issue: Mapped[Issue] = relationship(
        "Issue",
        back_populates="changelogs",
    )

    # Indexes
    __table_args__ = (
        Index("ix_changelogs_instance_changelog", "instance_id", "changelog_id", unique=True),
        Index("ix_changelogs_issue_created", "issue_id", "jira_created_at"),
        Index("ix_changelogs_tenant_instance", "tenant_id", "instance_id"),
        Index("ix_changelogs_items", "items", postgresql_using="gin"),
        Index("ix_changelogs_raw_jsonb", "raw_jsonb", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Changelog(id={self.id}, issue_key='{self.issue_key}', items={len(self.items)})>"


__all__ = ["Changelog"]

