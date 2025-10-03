"""Comment SQLAlchemy model."""

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


class Comment(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Comment SQLAlchemy model.

    Represents a Jira issue comment.
    """

    __tablename__ = "comments"

    # Foreign Keys
    instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("jira_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Jira instance this comment belongs to",
    )

    issue_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Issue this comment belongs to",
    )

    # Jira Identifiers
    comment_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Jira internal comment ID",
    )

    issue_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Issue key for quick lookup",
    )

    # Content
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Comment body (plain text or ADF)",
    )

    body_format: Mapped[str] = mapped_column(
        String(20),
        default="plain",
        nullable=False,
        doc="Body format: 'plain' or 'adf'",
    )

    # Author
    author_account_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Author Jira account ID",
    )

    # Visibility
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the comment is public",
    )

    visibility_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Visibility type: role, group",
    )

    visibility_value: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Visibility value (role or group name)",
    )

    # Timestamps
    jira_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the comment was created in Jira",
    )

    jira_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the comment was last updated in Jira",
    )

    # Raw Data
    raw_jsonb: Mapped[dict] = mapped_column(
        JSONBType,
        default=dict,
        nullable=False,
        doc="Full raw Jira comment JSON",
    )

    # Sync Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this comment was synced",
    )

    # Relationships
    instance: Mapped[JiraInstance] = relationship(
        "JiraInstance",
        back_populates="comments",
    )

    issue: Mapped[Issue] = relationship(
        "Issue",
        back_populates="comments",
    )

    # Indexes
    __table_args__ = (
        Index("ix_comments_instance_comment", "instance_id", "comment_id", unique=True),
        Index("ix_comments_issue_created", "issue_id", "jira_created_at"),
        Index("ix_comments_tenant_instance", "tenant_id", "instance_id"),
        Index("ix_comments_raw_jsonb", "raw_jsonb", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation."""
        body_preview = self.body[:50] + "..." if len(self.body) > 50 else self.body
        return f"<Comment(id={self.id}, issue_key='{self.issue_key}', body='{body_preview}')>"


__all__ = ["Comment"]

