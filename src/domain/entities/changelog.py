"""Changelog domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class ChangelogItem:
    """Individual field change within a changelog entry."""

    field: str  # Field name (e.g., "status", "assignee")
    field_type: str  # Field type (e.g., "jira", "custom")
    from_value: str | None = None
    from_string: str | None = None
    to_value: str | None = None
    to_string: str | None = None

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.field}: {self.from_string} → {self.to_string}"


@dataclass
class Changelog:
    """
    Changelog domain entity representing a Jira issue change history.

    This is a pure domain object with no framework dependencies.
    """

    # Identity
    id: UUID
    instance_id: UUID
    changelog_id: str  # Jira's internal changelog ID
    issue_key: str  # Parent issue key

    # Author
    author_account_id: str

    # Changes
    items: list[ChangelogItem] = field(default_factory=list)

    # Timestamp
    created_at: datetime | None = None

    # Metadata
    raw_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate changelog after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate changelog data.

        Raises:
            ValueError: If validation fails
        """
        if not self.changelog_id:
            raise ValueError("Changelog ID is required")

        if not self.issue_key:
            raise ValueError("Issue key is required")

        if not self.author_account_id:
            raise ValueError("Author account ID is required")

        if not self.items:
            raise ValueError("Changelog must have at least one item")

    def has_field_change(self, field: str) -> bool:
        """Check if a specific field was changed."""
        return any(item.field == field for item in self.items)

    def get_field_change(self, field: str) -> ChangelogItem | None:
        """Get the change for a specific field."""
        for item in self.items:
            if item.field == field:
                return item
        return None

    def get_status_change(self) -> ChangelogItem | None:
        """Get status change if present."""
        return self.get_field_change("status")

    def get_assignee_change(self) -> ChangelogItem | None:
        """Get assignee change if present."""
        return self.get_field_change("assignee")

    def is_status_change(self) -> bool:
        """Check if this changelog contains a status change."""
        return self.has_field_change("status")

    def is_assignee_change(self) -> bool:
        """Check if this changelog contains an assignee change."""
        return self.has_field_change("assignee")

    def __str__(self) -> str:
        """Human-readable string representation."""
        changes = ", ".join(item.field for item in self.items)
        return f"Changelog for {self.issue_key}: {changes}"

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"Changelog(id={self.id}, changelog_id='{self.changelog_id}', "
            f"issue_key='{self.issue_key}', items={len(self.items)})"
        )


__all__ = ["Changelog", "ChangelogItem"]

