"""User domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class User:
    """
    User domain entity representing a Jira user.

    This is a pure domain object with no framework dependencies.
    """

    # Identity
    id: UUID
    instance_id: UUID
    account_id: str  # Jira's account ID

    # Basic Information
    display_name: str

    # Account Type
    account_type: str = "atlassian"  # atlassian, app, customer
    email_address: str | None = None
    avatar_url: str | None = None

    # Status
    is_active: bool = True

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Metadata
    raw_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate user after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate user data.

        Raises:
            ValueError: If validation fails
        """
        if not self.account_id:
            raise ValueError("Account ID is required")

        if not self.display_name:
            raise ValueError("Display name is required")

        if self.email_address and not self.is_valid_email(self.email_address):
            raise ValueError(f"Invalid email address: {self.email_address}")

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Basic email validation.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        if not email or "@" not in email:
            return False

        parts = email.split("@")
        return len(parts) == 2 and all(parts)

    def is_atlassian_user(self) -> bool:
        """Check if this is an Atlassian user."""
        return self.account_type == "atlassian"

    def is_app_user(self) -> bool:
        """Check if this is an app/bot user."""
        return self.account_type == "app"

    def is_customer(self) -> bool:
        """Check if this is a customer user (service desk)."""
        return self.account_type == "customer"

    def deactivate(self) -> None:
        """Deactivate the user."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activate the user."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.display_name

    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"User(id={self.id}, account_id='{self.account_id}', "
            f"display_name='{self.display_name}', active={self.is_active})"
        )


__all__ = ["User"]

