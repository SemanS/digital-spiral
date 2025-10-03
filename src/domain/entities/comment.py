"""Comment domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class Comment:
    """
    Comment domain entity representing a Jira issue comment.

    This is a pure domain object with no framework dependencies.
    """

    # Identity
    id: UUID
    instance_id: UUID
    comment_id: str  # Jira's internal comment ID
    issue_key: str  # Parent issue key

    # Content
    body: str  # Plain text or ADF (Atlassian Document Format)

    # Author
    author_account_id: str

    # Format
    body_format: str = "plain"  # plain, adf

    # Visibility
    is_public: bool = True
    visibility_type: str | None = None  # role, group
    visibility_value: str | None = None  # e.g., "Administrators"

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Metadata
    raw_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate comment after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate comment data.

        Raises:
            ValueError: If validation fails
        """
        if not self.comment_id:
            raise ValueError("Comment ID is required")

        if not self.issue_key:
            raise ValueError("Issue key is required")

        if not self.body:
            raise ValueError("Comment body is required")

        if not self.author_account_id:
            raise ValueError("Author account ID is required")

    def is_adf_format(self) -> bool:
        """Check if comment uses ADF format."""
        return self.body_format == "adf"

    def is_restricted(self) -> bool:
        """Check if comment has restricted visibility."""
        return not self.is_public

    def restrict_to_role(self, role: str) -> None:
        """Restrict comment visibility to a specific role."""
        self.is_public = False
        self.visibility_type = "role"
        self.visibility_value = role
        self.updated_at = datetime.utcnow()

    def restrict_to_group(self, group: str) -> None:
        """Restrict comment visibility to a specific group."""
        self.is_public = False
        self.visibility_type = "group"
        self.visibility_value = group
        self.updated_at = datetime.utcnow()

    def make_public(self) -> None:
        """Make comment public."""
        self.is_public = True
        self.visibility_type = None
        self.visibility_value = None
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """Human-readable string representation."""
        preview = self.body[:50] + "..." if len(self.body) > 50 else self.body
        return f"Comment on {self.issue_key}: {preview}"

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"Comment(id={self.id}, comment_id='{self.comment_id}', "
            f"issue_key='{self.issue_key}', public={self.is_public})"
        )


__all__ = ["Comment"]

