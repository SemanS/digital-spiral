"""Project domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class Project:
    """
    Project domain entity representing a Jira project.

    This is a pure domain object with no framework dependencies.
    """

    # Identity
    id: UUID
    instance_id: UUID
    project_key: str  # e.g., "PROJ"
    project_id: str  # Jira's internal ID

    # Basic Information
    name: str
    description: str | None = None
    project_type: str = "software"  # software, service_desk, business

    # Configuration
    lead_account_id: str | None = None
    avatar_url: str | None = None
    url: str | None = None

    # Status
    is_archived: bool = False
    is_private: bool = False

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Metadata
    raw_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate project after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate project data.

        Raises:
            ValueError: If validation fails
        """
        if not self.project_key:
            raise ValueError("Project key is required")

        if not self.is_valid_project_key(self.project_key):
            raise ValueError(f"Invalid project key format: {self.project_key}")

        if not self.name:
            raise ValueError("Project name is required")

        if len(self.name) > 255:
            raise ValueError("Project name must be 255 characters or less")

    @staticmethod
    def is_valid_project_key(key: str) -> bool:
        """
        Check if project key has valid format (uppercase letters, 2-10 chars).

        Args:
            key: Project key to validate

        Returns:
            True if valid, False otherwise
        """
        if not key:
            return False

        # Project key must be uppercase letters only, 2-10 characters
        return key.isupper() and key.isalpha() and 2 <= len(key) <= 10

    def is_software_project(self) -> bool:
        """Check if this is a software project."""
        return self.project_type == "software"

    def is_service_desk_project(self) -> bool:
        """Check if this is a service desk project."""
        return self.project_type == "service_desk"

    def archive(self) -> None:
        """Archive the project."""
        self.is_archived = True
        self.updated_at = datetime.utcnow()

    def unarchive(self) -> None:
        """Unarchive the project."""
        self.is_archived = False
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.project_key}: {self.name}"

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"Project(id={self.id}, key='{self.project_key}', "
            f"name='{self.name}', type='{self.project_type}')"
        )


__all__ = ["Project"]

