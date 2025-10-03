"""Validation utilities."""

from __future__ import annotations

import re
from typing import Any

from pydantic import ValidationError


class ValidationException(Exception):
    """Validation exception."""

    def __init__(self, message: str, errors: dict[str, list[str]] | None = None):
        """
        Initialize exception.

        Args:
            message: Error message
            errors: Validation errors by field
        """
        self.message = message
        self.errors = errors or {}
        super().__init__(message)


class IssueKeyValidator:
    """Validator for Jira issue keys."""

    # Jira issue key pattern: PROJECT-123
    PATTERN = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")

    @classmethod
    def validate(cls, issue_key: str) -> bool:
        """
        Validate issue key format.

        Args:
            issue_key: Issue key to validate

        Returns:
            True if valid

        Raises:
            ValidationException: If invalid
        """
        if not issue_key:
            raise ValidationException("Issue key is required")

        if not cls.PATTERN.match(issue_key):
            raise ValidationException(
                f"Invalid issue key format: {issue_key}. "
                "Expected format: PROJECT-123"
            )

        return True


class ProjectKeyValidator:
    """Validator for Jira project keys."""

    # Jira project key pattern: 2-10 uppercase letters/numbers
    PATTERN = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")

    @classmethod
    def validate(cls, project_key: str) -> bool:
        """
        Validate project key format.

        Args:
            project_key: Project key to validate

        Returns:
            True if valid

        Raises:
            ValidationException: If invalid
        """
        if not project_key:
            raise ValidationException("Project key is required")

        if not cls.PATTERN.match(project_key):
            raise ValidationException(
                f"Invalid project key format: {project_key}. "
                "Expected: 2-10 uppercase letters/numbers"
            )

        return True


class PaginationValidator:
    """Validator for pagination parameters."""

    MAX_LIMIT = 100
    DEFAULT_LIMIT = 50

    @classmethod
    def validate(cls, skip: int, limit: int) -> tuple[int, int]:
        """
        Validate and normalize pagination parameters.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            Tuple of (skip, limit)

        Raises:
            ValidationException: If invalid
        """
        errors = {}

        # Validate skip
        if skip < 0:
            errors["skip"] = ["Skip must be >= 0"]

        # Validate limit
        if limit < 1:
            errors["limit"] = ["Limit must be >= 1"]
        elif limit > cls.MAX_LIMIT:
            errors["limit"] = [f"Limit must be <= {cls.MAX_LIMIT}"]

        if errors:
            raise ValidationException("Invalid pagination parameters", errors)

        return skip, limit


class SearchQueryValidator:
    """Validator for search queries."""

    MIN_LENGTH = 2
    MAX_LENGTH = 500

    @classmethod
    def validate(cls, query: str | None) -> str | None:
        """
        Validate search query.

        Args:
            query: Search query

        Returns:
            Validated query

        Raises:
            ValidationException: If invalid
        """
        if query is None:
            return None

        query = query.strip()

        if not query:
            return None

        if len(query) < cls.MIN_LENGTH:
            raise ValidationException(
                f"Search query must be at least {cls.MIN_LENGTH} characters"
            )

        if len(query) > cls.MAX_LENGTH:
            raise ValidationException(
                f"Search query must be at most {cls.MAX_LENGTH} characters"
            )

        return query


class DTOValidator:
    """Validator for DTOs using Pydantic."""

    @classmethod
    def validate_dto(cls, dto_class: type, data: dict[str, Any]) -> Any:
        """
        Validate data against DTO schema.

        Args:
            dto_class: DTO class (Pydantic model)
            data: Data to validate

        Returns:
            Validated DTO instance

        Raises:
            ValidationException: If validation fails
        """
        try:
            return dto_class(**data)
        except ValidationError as e:
            # Convert Pydantic errors to our format
            errors = {}
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                if field not in errors:
                    errors[field] = []
                errors[field].append(error["msg"])

            raise ValidationException("Validation failed", errors)


__all__ = [
    "ValidationException",
    "IssueKeyValidator",
    "ProjectKeyValidator",
    "PaginationValidator",
    "SearchQueryValidator",
    "DTOValidator",
]

