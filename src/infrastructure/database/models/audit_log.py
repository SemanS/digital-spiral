"""Audit Log model for tracking all write operations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    pass


class AuditLog(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Audit Log model for tracking all write operations.

    Records all create, update, delete operations for compliance and debugging.
    Includes user context, resource details, and change details.
    """

    __tablename__ = "audit_logs"

    # User Context
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        doc="User who performed the action (email or account ID)",
    )

    # Action Details
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Action performed: create, update, delete, transition, etc.",
    )

    # Resource Details
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Type of resource: issue, instance, project, etc.",
    )

    resource_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="ID or key of the resource (e.g., issue key, instance ID)",
    )

    # Change Details
    changes: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="JSON object with before/after values for changed fields",
    )

    # Request Context
    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="Request ID for tracing (from headers or generated)",
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address of the client (IPv4 or IPv6)",
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="User agent string from the request",
    )

    # Metadata
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="Additional metadata (instance_id, tool_name, etc.)",
    )

    # Timestamp (from TimestampMixin, but we'll use created_at as the audit timestamp)
    # created_at is automatically set by TimestampMixin

    # Indexes
    __table_args__ = (
        Index("ix_audit_logs_tenant_timestamp", "tenant_id", "created_at"),
        Index("ix_audit_logs_tenant_resource", "tenant_id", "resource_type", "resource_id"),
        Index("ix_audit_logs_tenant_action", "tenant_id", "action"),
        Index("ix_audit_logs_user_timestamp", "user_id", "created_at"),
        Index("ix_audit_logs_changes", "changes", postgresql_using="gin"),
        Index("ix_audit_logs_metadata", "metadata", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"resource='{self.resource_type}:{self.resource_id}', "
            f"user='{self.user_id}')>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.action} on {self.resource_type} {self.resource_id} by {self.user_id}"


__all__ = ["AuditLog"]

