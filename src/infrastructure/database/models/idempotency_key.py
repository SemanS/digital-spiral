"""Idempotency Key model for ensuring idempotent write operations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin, JSONBType

if TYPE_CHECKING:
    pass


class IdempotencyKey(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Idempotency Key model for ensuring idempotent write operations.

    Stores the result of write operations keyed by idempotency key.
    Allows clients to safely retry operations without duplicating data.
    Keys expire after 24 hours.
    """

    __tablename__ = "idempotency_keys"

    # Idempotency Key
    key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Client-provided idempotency key (unique per tenant + operation)",
    )

    # Operation Details
    operation: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Operation type: create_issue, update_issue, add_comment, etc.",
    )

    # Result
    result: Mapped[dict] = mapped_column(
        JSONBType,
        default=dict,
        nullable=False,
        doc="JSON result of the operation (response body)",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="completed",
        doc="Status: completed, failed, processing",
    )

    # Error (if failed)
    error: Mapped[dict | None] = mapped_column(
        JSONBType,
        nullable=True,
        doc="Error details if the operation failed",
    )

    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="When this key expires (typically 24 hours from creation)",
    )

    # Request Context
    request_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Request ID for tracing",
    )

    # Indexes
    __table_args__ = (
        # Unique constraint on tenant_id + operation + key
        Index(
            "ix_idempotency_keys_tenant_operation_key",
            "tenant_id",
            "operation",
            "key",
            unique=True,
        ),
        Index("ix_idempotency_keys_expires_at", "expires_at"),
        Index("ix_idempotency_keys_tenant_created", "tenant_id", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<IdempotencyKey(id={self.id}, key='{self.key}', "
            f"operation='{self.operation}', status='{self.status}')>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Idempotency key {self.key} for {self.operation}"

    @property
    def is_expired(self) -> bool:
        """Check if the key has expired."""
        from datetime import timezone

        return datetime.now(timezone.utc) > self.expires_at


__all__ = ["IdempotencyKey"]

