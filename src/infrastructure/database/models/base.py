"""Base SQLAlchemy models and mixins."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class JSONBType(TypeDecorator):
    """JSONB type that falls back to JSON for SQLite."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class ArrayType(TypeDecorator):
    """ARRAY type that falls back to JSON for SQLite."""

    impl = JSON
    cache_ok = True

    def __init__(self, item_type=String, *args, **kwargs):
        self.item_type = item_type
        super().__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Type annotation map for common types
    type_annotation_map = {
        str: String,
        datetime: DateTime(timezone=True),
    }


class UUIDMixin:
    """Mixin for UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="Unique identifier (UUID v4)",
    )


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when the record was last updated",
    )


class TenantMixin:
    """Mixin for multi-tenant isolation."""

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="Tenant identifier for multi-tenant isolation",
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft deleted (NULL if not deleted)",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None


def to_dict(obj: Any, exclude: set[str] | None = None) -> dict[str, Any]:
    """
    Convert SQLAlchemy model instance to dictionary.

    Args:
        obj: SQLAlchemy model instance
        exclude: Set of column names to exclude from the result

    Returns:
        Dictionary representation of the model
    """
    exclude = exclude or set()
    result = {}

    for column in obj.__table__.columns:
        if column.name not in exclude:
            value = getattr(obj, column.name)
            # Convert datetime to ISO format
            if isinstance(value, datetime):
                value = value.isoformat()
            # Convert UUID to string
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value

    return result


__all__ = [
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    "TenantMixin",
    "SoftDeleteMixin",
    "to_dict",
]

