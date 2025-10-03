"""Tenant model for multi-tenant isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .jira_instance import JiraInstance


class Tenant(Base, UUIDMixin, TimestampMixin):
    """
    Tenant model for multi-tenant isolation.

    Each tenant represents a separate organization or customer using Digital Spiral.
    All data is isolated by tenant_id to ensure data privacy and security.
    """

    __tablename__ = "tenants"

    # Basic Information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Tenant name (organization or customer name)",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="URL-safe slug for the tenant (e.g., 'acme-corp')",
    )

    # Contact Information
    contact_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Primary contact email for the tenant",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the tenant is active (can be disabled for suspension)",
    )

    # Configuration
    settings: Mapped[dict | None] = mapped_column(
        Text,
        nullable=True,
        doc="JSON-encoded tenant-specific settings",
    )

    # Relationships
    jira_instances: Mapped[list[JiraInstance]] = relationship(
        "JiraInstance",
        back_populates="tenant",
        cascade="all, delete-orphan",
        doc="Jira instances connected to this tenant",
    )

    def __repr__(self) -> str:
        """String representation of the tenant."""
        return f"<Tenant(id={self.id}, slug='{self.slug}', name='{self.name}')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.name} ({self.slug})"


__all__ = ["Tenant"]

