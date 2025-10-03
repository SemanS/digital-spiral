"""Jira Instance model for managing Jira Cloud connections."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .changelog import Changelog
    from .comment import Comment
    from .issue import Issue
    from .project import Project
    from .tenant import Tenant
    from .user import User


class JiraInstance(Base, UUIDMixin, TimestampMixin):
    """
    Jira Instance model for managing Jira Cloud connections.

    Each tenant can have multiple Jira instances (e.g., production, staging).
    Stores connection details, credentials, and sync status.
    """

    __tablename__ = "jira_instances"

    # Tenant Relationship
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant that owns this Jira instance",
    )

    tenant: Mapped[Tenant] = relationship(
        "Tenant",
        back_populates="jira_instances",
    )

    # Jira Instance Details
    base_url: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Jira Cloud base URL (e.g., 'https://your-domain.atlassian.net')",
    )

    site_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Atlassian site ID (cloud ID)",
    )

    # Authentication
    auth_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="api_token",
        doc="Authentication type: 'api_token', 'oauth2', 'basic'",
    )

    auth_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Email for API token authentication",
    )

    # Encrypted credentials (should be encrypted at rest)
    encrypted_credentials: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Encrypted API token or OAuth credentials (JSON)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this instance is active",
    )

    is_connected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether connection to Jira is currently working",
    )

    last_connection_check: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time connection was verified",
    )

    connection_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Last connection error message (if any)",
    )

    # Sync Configuration
    sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether automatic sync is enabled",
    )

    sync_interval_minutes: Mapped[int] = mapped_column(
        default=5,
        nullable=False,
        doc="Sync interval in minutes (for polling fallback)",
    )

    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last successful sync timestamp",
    )

    last_sync_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Last sync error message (if any)",
    )

    # Webhook Configuration
    webhook_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Webhook URL registered in Jira",
    )

    webhook_secret: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Webhook secret for signature verification",
    )

    webhook_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether webhooks are enabled and registered",
    )

    # Rate Limiting
    rate_limit_per_second: Mapped[int] = mapped_column(
        default=10,
        nullable=False,
        doc="Maximum API requests per second",
    )

    # Metadata
    jira_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Jira version (e.g., 'Cloud', '9.4.0')",
    )

    capabilities: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON-encoded Jira capabilities (features available)",
    )

    # Relationships
    issues: Mapped[list[Issue]] = relationship(
        "Issue",
        back_populates="instance",
        cascade="all, delete-orphan",
    )

    projects: Mapped[list[Project]] = relationship(
        "Project",
        back_populates="instance",
        cascade="all, delete-orphan",
    )

    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="instance",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list[Comment]] = relationship(
        "Comment",
        back_populates="instance",
        cascade="all, delete-orphan",
    )

    changelogs: Mapped[list[Changelog]] = relationship(
        "Changelog",
        back_populates="instance",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of the Jira instance."""
        return f"<JiraInstance(id={self.id}, base_url='{self.base_url}', tenant_id={self.tenant_id})>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Jira Instance: {self.base_url}"


__all__ = ["JiraInstance"]

