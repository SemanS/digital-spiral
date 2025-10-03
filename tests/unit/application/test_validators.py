"""Unit tests for validators."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from src.application.validation import (
    DTOValidator,
    IssueKeyValidator,
    PaginationValidator,
    ProjectKeyValidator,
    SearchQueryValidator,
    ValidationException,
)


class TestIssueKeyValidator:
    """Tests for IssueKeyValidator."""

    def test_valid_issue_key(self):
        """Test valid issue key."""
        assert IssueKeyValidator.validate("PROJ-123") is True
        assert IssueKeyValidator.validate("ABC-1") is True
        assert IssueKeyValidator.validate("TEST123-999") is True

    def test_invalid_issue_key_format(self):
        """Test invalid issue key format."""
        with pytest.raises(ValidationException):
            IssueKeyValidator.validate("proj-123")  # lowercase

        with pytest.raises(ValidationException):
            IssueKeyValidator.validate("PROJ123")  # no dash

        with pytest.raises(ValidationException):
            IssueKeyValidator.validate("PROJ-")  # no number

        with pytest.raises(ValidationException):
            IssueKeyValidator.validate("-123")  # no project

    def test_empty_issue_key(self):
        """Test empty issue key."""
        with pytest.raises(ValidationException):
            IssueKeyValidator.validate("")


class TestProjectKeyValidator:
    """Tests for ProjectKeyValidator."""

    def test_valid_project_key(self):
        """Test valid project key."""
        assert ProjectKeyValidator.validate("PROJ") is True
        assert ProjectKeyValidator.validate("AB") is True
        assert ProjectKeyValidator.validate("TEST123") is True
        assert ProjectKeyValidator.validate("A1B2C3D4E5") is True  # 10 chars

    def test_invalid_project_key_format(self):
        """Test invalid project key format."""
        with pytest.raises(ValidationException):
            ProjectKeyValidator.validate("proj")  # lowercase

        with pytest.raises(ValidationException):
            ProjectKeyValidator.validate("A")  # too short

        with pytest.raises(ValidationException):
            ProjectKeyValidator.validate("A1B2C3D4E5F")  # too long (11 chars)

        with pytest.raises(ValidationException):
            ProjectKeyValidator.validate("1ABC")  # starts with number

    def test_empty_project_key(self):
        """Test empty project key."""
        with pytest.raises(ValidationException):
            ProjectKeyValidator.validate("")


class TestPaginationValidator:
    """Tests for PaginationValidator."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        skip, limit = PaginationValidator.validate(0, 50)
        assert skip == 0
        assert limit == 50

        skip, limit = PaginationValidator.validate(10, 100)
        assert skip == 10
        assert limit == 100

    def test_invalid_skip(self):
        """Test invalid skip parameter."""
        with pytest.raises(ValidationException) as exc_info:
            PaginationValidator.validate(-1, 50)

        assert "skip" in exc_info.value.errors

    def test_invalid_limit_too_small(self):
        """Test invalid limit (too small)."""
        with pytest.raises(ValidationException) as exc_info:
            PaginationValidator.validate(0, 0)

        assert "limit" in exc_info.value.errors

    def test_invalid_limit_too_large(self):
        """Test invalid limit (too large)."""
        with pytest.raises(ValidationException) as exc_info:
            PaginationValidator.validate(0, 101)

        assert "limit" in exc_info.value.errors

    def test_multiple_errors(self):
        """Test multiple validation errors."""
        with pytest.raises(ValidationException) as exc_info:
            PaginationValidator.validate(-1, 0)

        assert "skip" in exc_info.value.errors
        assert "limit" in exc_info.value.errors


class TestSearchQueryValidator:
    """Tests for SearchQueryValidator."""

    def test_valid_query(self):
        """Test valid search query."""
        assert SearchQueryValidator.validate("bug") == "bug"
        assert SearchQueryValidator.validate("  test  ") == "test"
        assert SearchQueryValidator.validate("a" * 500) == "a" * 500

    def test_none_query(self):
        """Test None query."""
        assert SearchQueryValidator.validate(None) is None

    def test_empty_query(self):
        """Test empty query."""
        assert SearchQueryValidator.validate("") is None
        assert SearchQueryValidator.validate("   ") is None

    def test_query_too_short(self):
        """Test query too short."""
        with pytest.raises(ValidationException):
            SearchQueryValidator.validate("a")

    def test_query_too_long(self):
        """Test query too long."""
        with pytest.raises(ValidationException):
            SearchQueryValidator.validate("a" * 501)


class TestDTOValidator:
    """Tests for DTOValidator."""

    class SampleDTO(BaseModel):
        """Sample DTO for testing."""
        name: str
        age: int
        email: str | None = None

    def test_valid_dto(self):
        """Test valid DTO validation."""
        data = {"name": "John", "age": 30}
        dto = DTOValidator.validate_dto(self.SampleDTO, data)

        assert dto.name == "John"
        assert dto.age == 30
        assert dto.email is None

    def test_invalid_dto_missing_field(self):
        """Test invalid DTO (missing required field)."""
        data = {"name": "John"}

        with pytest.raises(ValidationException) as exc_info:
            DTOValidator.validate_dto(self.SampleDTO, data)

        assert "age" in exc_info.value.errors

    def test_invalid_dto_wrong_type(self):
        """Test invalid DTO (wrong type)."""
        data = {"name": "John", "age": "thirty"}

        with pytest.raises(ValidationException) as exc_info:
            DTOValidator.validate_dto(self.SampleDTO, data)

        assert "age" in exc_info.value.errors

    def test_invalid_dto_multiple_errors(self):
        """Test invalid DTO (multiple errors)."""
        data = {"age": "thirty"}

        with pytest.raises(ValidationException) as exc_info:
            DTOValidator.validate_dto(self.SampleDTO, data)

        assert "name" in exc_info.value.errors
        assert "age" in exc_info.value.errors

