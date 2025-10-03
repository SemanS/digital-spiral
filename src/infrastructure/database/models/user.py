"""User SQLAlchemy model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin, JSONBType

if TYPE_CHECKING:
    from .jira_instance import JiraInstance


class User(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    User SQLAlchemy model.

    Represents a Jira user.
    """

    __tablename__ = "users"

    # Foreign Keys
    instance_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("jira_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Jira instance this user belongs to",
    )

    # Jira Identifiers
    account_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Jira account ID",
    )

    account_type: Mapped[str] = mapped_column(
        String(50),
        default="atlassian",
        nullable=False,
        doc="Account type: atlassian, app, customer",
    )

    # Basic Information
    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User display name",
    )

    email_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="User email address",
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="User avatar URL",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the user is active",
    )

    # Timestamps
    jira_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the user was created in Jira",
    )

    jira_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the user was last updated in Jira",
    )

    # Raw Data
    raw_jsonb: Mapped[dict] = mapped_column(
        JSONBType,
        default=dict,
        nullable=False,
        doc="Full raw Jira user JSON",
    )

    # Sync Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this user was synced",
    )

    # Relationships
    instance: Mapped[JiraInstance] = relationship(
        "JiraInstance",
        back_populates="users",
    )

    # Indexes
    __table_args__ = (
        Index("ix_users_instance_account", "instance_id", "account_id", unique=True),
        Index("ix_users_tenant_instance", "tenant_id", "instance_id"),
        Index("ix_users_raw_jsonb", "raw_jsonb", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, account_id='{self.account_id}', display_name='{self.display_name}')>"


__all__ = ["User"]

