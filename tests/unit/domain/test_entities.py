"""Unit tests for domain entities."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from src.domain.entities import Changelog, ChangelogItem, Comment, Issue, Project, User


class TestIssueEntity:
    """Tests for Issue entity."""

    def test_create_issue(self):
        """Test creating a valid issue."""
        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-123",
            issue_id="10001",
            summary="Test issue",
            project_key="PROJ",
        )

        assert issue.issue_key == "PROJ-123"
        assert issue.summary == "Test issue"
        assert issue.status == "To Do"

    def test_issue_key_validation(self):
        """Test issue key validation."""
        assert Issue.is_valid_issue_key("PROJ-123") is True
        assert Issue.is_valid_issue_key("ABC-1") is True
        assert Issue.is_valid_issue_key("invalid") is False
        assert Issue.is_valid_issue_key("proj-123") is False  # lowercase
        assert Issue.is_valid_issue_key("PROJ") is False  # no number

    def test_issue_requires_key(self):
        """Test that issue requires a key."""
        with pytest.raises(ValueError, match="Issue key is required"):
            Issue(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                issue_key="",
                issue_id="10001",
                summary="Test",
            )

    def test_issue_requires_summary(self):
        """Test that issue requires a summary."""
        with pytest.raises(ValueError, match="Summary is required"):
            Issue(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                issue_key="PROJ-123",
                issue_id="10001",
                summary="",
            )

    def test_issue_is_subtask(self):
        """Test subtask detection."""
        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-123",
            issue_id="10001",
            summary="Test",
            parent_key="PROJ-100",
        )

        assert issue.is_subtask() is True

    def test_issue_transition(self):
        """Test issue status transition."""
        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-123",
            issue_id="10001",
            summary="Test",
            status="To Do",
        )

        assert issue.can_transition_to("In Progress") is True
        issue.transition_to("In Progress")
        assert issue.status == "In Progress"

    def test_issue_invalid_transition(self):
        """Test invalid status transition."""
        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-123",
            issue_id="10001",
            summary="Test",
            status="To Do",
        )

        with pytest.raises(ValueError, match="Cannot transition"):
            issue.transition_to("In Review")

    def test_issue_labels(self):
        """Test issue label management."""
        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-123",
            issue_id="10001",
            summary="Test",
        )

        issue.add_label("bug")
        assert issue.has_label("bug") is True

        issue.remove_label("bug")
        assert issue.has_label("bug") is False


class TestProjectEntity:
    """Tests for Project entity."""

    def test_create_project(self):
        """Test creating a valid project."""
        project = Project(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            project_key="PROJ",
            project_id="10000",
            name="Test Project",
        )

        assert project.project_key == "PROJ"
        assert project.name == "Test Project"

    def test_project_key_validation(self):
        """Test project key validation."""
        assert Project.is_valid_project_key("PROJ") is True
        assert Project.is_valid_project_key("ABC") is True
        assert Project.is_valid_project_key("ABCDEFGHIJ") is True  # 10 chars
        assert Project.is_valid_project_key("A") is False  # too short
        assert Project.is_valid_project_key("ABCDEFGHIJK") is False  # too long
        assert Project.is_valid_project_key("proj") is False  # lowercase
        assert Project.is_valid_project_key("PROJ123") is False  # contains numbers

    def test_project_requires_key(self):
        """Test that project requires a key."""
        with pytest.raises(ValueError, match="Project key is required"):
            Project(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                project_key="",
                project_id="10000",
                name="Test",
            )

    def test_project_archive(self):
        """Test project archiving."""
        project = Project(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            project_key="PROJ",
            project_id="10000",
            name="Test",
        )

        assert project.is_archived is False
        project.archive()
        assert project.is_archived is True

        project.unarchive()
        assert project.is_archived is False


class TestUserEntity:
    """Tests for User entity."""

    def test_create_user(self):
        """Test creating a valid user."""
        user = User(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            account_id="account123",
            display_name="John Doe",
            email_address="john@example.com",
        )

        assert user.account_id == "account123"
        assert user.display_name == "John Doe"
        assert user.is_active is True

    def test_email_validation(self):
        """Test email validation."""
        assert User.is_valid_email("test@example.com") is True
        assert User.is_valid_email("invalid") is False
        assert User.is_valid_email("@example.com") is False
        assert User.is_valid_email("test@") is False

    def test_user_requires_account_id(self):
        """Test that user requires account ID."""
        with pytest.raises(ValueError, match="Account ID is required"):
            User(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                account_id="",
                display_name="Test",
            )

    def test_user_deactivation(self):
        """Test user deactivation."""
        user = User(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            account_id="account123",
            display_name="Test",
        )

        assert user.is_active is True
        user.deactivate()
        assert user.is_active is False

        user.activate()
        assert user.is_active is True


class TestCommentEntity:
    """Tests for Comment entity."""

    def test_create_comment(self):
        """Test creating a valid comment."""
        comment = Comment(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            comment_id="10001",
            issue_key="PROJ-123",
            body="This is a comment",
            author_account_id="account123",
        )

        assert comment.comment_id == "10001"
        assert comment.body == "This is a comment"
        assert comment.is_public is True

    def test_comment_requires_body(self):
        """Test that comment requires body."""
        with pytest.raises(ValueError, match="Comment body is required"):
            Comment(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                comment_id="10001",
                issue_key="PROJ-123",
                body="",
                author_account_id="account123",
            )

    def test_comment_visibility(self):
        """Test comment visibility restrictions."""
        comment = Comment(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            comment_id="10001",
            issue_key="PROJ-123",
            body="Test",
            author_account_id="account123",
        )

        assert comment.is_restricted() is False

        comment.restrict_to_role("Administrators")
        assert comment.is_restricted() is True
        assert comment.visibility_type == "role"
        assert comment.visibility_value == "Administrators"

        comment.make_public()
        assert comment.is_restricted() is False


class TestChangelogEntity:
    """Tests for Changelog entity."""

    def test_create_changelog(self):
        """Test creating a valid changelog."""
        item = ChangelogItem(
            field="status",
            field_type="jira",
            from_string="To Do",
            to_string="In Progress",
        )

        changelog = Changelog(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            changelog_id="10001",
            issue_key="PROJ-123",
            author_account_id="account123",
            items=[item],
        )

        assert changelog.changelog_id == "10001"
        assert len(changelog.items) == 1

    def test_changelog_requires_items(self):
        """Test that changelog requires items."""
        with pytest.raises(ValueError, match="at least one item"):
            Changelog(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                changelog_id="10001",
                issue_key="PROJ-123",
                author_account_id="account123",
                items=[],
            )

    def test_changelog_field_detection(self):
        """Test changelog field change detection."""
        status_item = ChangelogItem(
            field="status",
            field_type="jira",
            from_string="To Do",
            to_string="In Progress",
        )

        changelog = Changelog(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            changelog_id="10001",
            issue_key="PROJ-123",
            author_account_id="account123",
            items=[status_item],
        )

        assert changelog.has_field_change("status") is True
        assert changelog.has_field_change("assignee") is False
        assert changelog.is_status_change() is True

