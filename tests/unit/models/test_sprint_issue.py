"""Unit tests for SprintIssue model."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.infrastructure.database.models import SprintIssue


class TestSprintIssue:
    """Test SprintIssue model."""

    def test_sprint_issue_creation(self):
        """Test creating a SprintIssue instance."""
        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=datetime.utcnow(),
            story_points=5.0,
            completed=True,
        )

        assert sprint_issue.story_points == 5.0
        assert sprint_issue.completed is True
        assert sprint_issue.removed_at is None

    def test_sprint_issue_repr(self):
        """Test SprintIssue __repr__ method."""
        sprint_id = uuid4()
        issue_id = uuid4()

        sprint_issue = SprintIssue(
            sprint_id=sprint_id,
            issue_id=issue_id,
            added_at=datetime.utcnow(),
            completed=True,
        )

        repr_str = repr(sprint_issue)
        assert "SprintIssue" in repr_str
        assert str(sprint_id) in repr_str
        assert str(issue_id) in repr_str
        assert "True" in repr_str

    def test_was_removed_property_false(self):
        """Test was_removed property when not removed."""
        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=datetime.utcnow(),
        )

        assert sprint_issue.was_removed is False

    def test_was_removed_property_true(self):
        """Test was_removed property when removed."""
        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=datetime.utcnow(),
            removed_at=datetime.utcnow() + timedelta(days=5),
        )

        assert sprint_issue.was_removed is True

    def test_duration_in_sprint_days(self):
        """Test duration_in_sprint_days property."""
        added = datetime.utcnow()
        removed = added + timedelta(days=7)

        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=added,
            removed_at=removed,
        )

        assert sprint_issue.duration_in_sprint_days == 7

    def test_duration_in_sprint_days_none_when_not_removed(self):
        """Test duration_in_sprint_days returns None when not removed."""
        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=datetime.utcnow(),
        )

        assert sprint_issue.duration_in_sprint_days is None

    def test_sprint_issue_without_story_points(self):
        """Test sprint issue without story points."""
        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=datetime.utcnow(),
        )

        assert sprint_issue.story_points is None

    def test_sprint_issue_not_completed_by_default(self):
        """Test sprint issue is not completed by default."""
        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=datetime.utcnow(),
        )

        assert sprint_issue.completed is False

    def test_sprint_issue_with_fractional_story_points(self):
        """Test sprint issue with fractional story points."""
        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=datetime.utcnow(),
            story_points=2.5,
        )

        assert sprint_issue.story_points == 2.5

    def test_sprint_issue_completed_and_removed(self):
        """Test sprint issue that was completed and then removed."""
        added = datetime.utcnow()
        removed = added + timedelta(days=3)

        sprint_issue = SprintIssue(
            sprint_id=uuid4(),
            issue_id=uuid4(),
            added_at=added,
            removed_at=removed,
            story_points=8.0,
            completed=True,
        )

        assert sprint_issue.completed is True
        assert sprint_issue.was_removed is True
        assert sprint_issue.duration_in_sprint_days == 3
        assert sprint_issue.story_points == 8.0

