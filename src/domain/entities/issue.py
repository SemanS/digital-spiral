"""Issue domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class Issue:
    """
    Issue domain entity representing a Jira issue.

    This is a pure domain object with no framework dependencies.
    Contains business logic and validation rules.
    """

    # Identity
    id: UUID
    instance_id: UUID
    issue_key: str  # e.g., "PROJ-123"
    issue_id: str  # Jira's internal ID

    # Basic Information
    summary: str
    description: str | None = None
    issue_type: str = "Task"  # Task, Bug, Story, Epic, etc.

    # Status & Priority
    status: str = "To Do"
    priority: str = "Medium"

    # Assignment
    assignee_account_id: str | None = None
    reporter_account_id: str | None = None

    # Project & Parent
    project_key: str = ""
    parent_key: str | None = None  # For subtasks

    # Labels & Components
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    # Custom Fields & Raw Data
    custom_fields: dict[str, Any] = field(default_factory=dict)
    raw_data: dict[str, Any] = field(default_factory=dict)

    # Metadata
    version: int = 1  # For optimistic locking

    def __post_init__(self) -> None:
        """Validate issue after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate issue data.

        Raises:
            ValueError: If validation fails
        """
        if not self.issue_key:
            raise ValueError("Issue key is required")

        if not self.is_valid_issue_key(self.issue_key):
            raise ValueError(f"Invalid issue key format: {self.issue_key}")

        if not self.summary:
            raise ValueError("Summary is required")

        if len(self.summary) > 255:
            raise ValueError("Summary must be 255 characters or less")

    @staticmethod
    def is_valid_issue_key(key: str) -> bool:
        """
        Check if issue key has valid format (PROJECT-123).

        Args:
            key: Issue key to validate

        Returns:
            True if valid, False otherwise
        """
        if not key or "-" not in key:
            return False

        parts = key.split("-")
        if len(parts) != 2:
            return False

        project_key, issue_number = parts
        return project_key.isupper() and issue_number.isdigit()

    def is_subtask(self) -> bool:
        """Check if this issue is a subtask."""
        return self.parent_key is not None

    def is_resolved(self) -> bool:
        """Check if this issue is resolved."""
        return self.resolved_at is not None

    def is_assigned(self) -> bool:
        """Check if this issue is assigned to someone."""
        return self.assignee_account_id is not None

    def has_label(self, label: str) -> bool:
        """Check if issue has a specific label."""
        return label in self.labels

    def add_label(self, label: str) -> None:
        """Add a label to the issue."""
        if label not in self.labels:
            self.labels.append(label)

    def remove_label(self, label: str) -> None:
        """Remove a label from the issue."""
        if label in self.labels:
            self.labels.remove(label)

    def can_transition_to(self, new_status: str) -> bool:
        """
        Check if issue can transition to a new status.

        This is a simplified version. In production, this would check
        the workflow configuration from Jira.

        Args:
            new_status: Target status

        Returns:
            True if transition is allowed
        """
        # Simplified workflow rules
        allowed_transitions = {
            "To Do": ["In Progress", "Done"],
            "In Progress": ["To Do", "Done", "In Review"],
            "In Review": ["In Progress", "Done"],
            "Done": ["To Do"],  # Reopen
        }

        return new_status in allowed_transitions.get(self.status, [])

    def transition_to(self, new_status: str) -> None:
        """
        Transition issue to a new status.

        Args:
            new_status: Target status

        Raises:
            ValueError: If transition is not allowed
        """
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from '{self.status}' to '{new_status}'"
            )

        self.status = new_status
        self.updated_at = datetime.utcnow()

        # Mark as resolved if transitioning to Done
        if new_status == "Done" and not self.resolved_at:
            self.resolved_at = datetime.utcnow()

    def assign_to(self, account_id: str) -> None:
        """Assign issue to a user."""
        self.assignee_account_id = account_id
        self.updated_at = datetime.utcnow()

    def unassign(self) -> None:
        """Unassign issue."""
        self.assignee_account_id = None
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.issue_key}: {self.summary}"

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"Issue(id={self.id}, key='{self.issue_key}', "
            f"summary='{self.summary[:50]}...', status='{self.status}')"
        )


__all__ = ["Issue"]

