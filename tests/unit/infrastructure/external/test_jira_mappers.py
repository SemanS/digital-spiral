"""Unit tests for Jira data mappers."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from src.domain.entities import Changelog, Comment, Issue, Project, User
from src.infrastructure.external.jira.mappers import (
    JiraChangelogMapper,
    JiraCommentMapper,
    JiraIssueMapper,
    JiraProjectMapper,
    JiraUserMapper,
    parse_datetime,
    safe_get,
)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_parse_datetime_valid(self):
        """Test parsing valid datetime."""
        result = parse_datetime("2024-01-15T10:30:00.000Z")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_datetime_none(self):
        """Test parsing None."""
        result = parse_datetime(None)
        assert result is None

    def test_parse_datetime_invalid(self):
        """Test parsing invalid datetime."""
        result = parse_datetime("invalid")
        assert result is None

    def test_safe_get_simple(self):
        """Test safe_get with simple key."""
        data = {"key": "value"}
        result = safe_get(data, "key")
        assert result == "value"

    def test_safe_get_nested(self):
        """Test safe_get with nested keys."""
        data = {"level1": {"level2": {"level3": "value"}}}
        result = safe_get(data, "level1", "level2", "level3")
        assert result == "value"

    def test_safe_get_missing(self):
        """Test safe_get with missing key."""
        data = {"key": "value"}
        result = safe_get(data, "missing", default="default")
        assert result == "default"

    def test_safe_get_none_in_path(self):
        """Test safe_get when intermediate value is None."""
        data = {"level1": None}
        result = safe_get(data, "level1", "level2", default="default")
        assert result == "default"


class TestJiraIssueMapper:
    """Tests for JiraIssueMapper."""

    @pytest.fixture
    def jira_issue_data(self):
        """Sample Jira issue data."""
        return {
            "id": "10001",
            "key": "PROJ-123",
            "fields": {
                "summary": "Test issue",
                "description": "Test description",
                "issuetype": {"name": "Bug"},
                "status": {
                    "name": "In Progress",
                    "statusCategory": {"name": "In Progress"}
                },
                "priority": {"name": "High"},
                "assignee": {"accountId": "user123"},
                "reporter": {"accountId": "user456"},
                "project": {"key": "PROJ", "id": "10000"},
                "labels": ["bug", "urgent"],
                "components": [{"name": "Backend"}, {"name": "API"}],
                "created": "2024-01-15T10:00:00.000Z",
                "updated": "2024-01-15T12:00:00.000Z",
                "resolutiondate": None,
                "customfield_10001": "custom value",
            }
        }

    def test_to_entity(self, jira_issue_data):
        """Test converting Jira issue to entity."""
        instance_id = uuid.uuid4()
        issue = JiraIssueMapper.to_entity(jira_issue_data, instance_id)

        assert isinstance(issue, Issue)
        assert issue.instance_id == instance_id
        assert issue.issue_key == "PROJ-123"
        assert issue.issue_id == "10001"
        assert issue.summary == "Test issue"
        assert issue.description == "Test description"
        assert issue.issue_type == "Bug"
        assert issue.status == "In Progress"
        assert issue.priority == "High"
        assert issue.assignee_account_id == "user123"
        assert issue.reporter_account_id == "user456"
        assert issue.project_key == "PROJ"
        assert issue.labels == ["bug", "urgent"]
        assert issue.components == ["Backend", "API"]
        assert issue.custom_fields["customfield_10001"] == "custom value"
        assert issue.raw_data == jira_issue_data

    def test_to_entity_minimal(self):
        """Test converting minimal Jira issue."""
        instance_id = uuid.uuid4()
        minimal_data = {
            "id": "10001",
            "key": "PROJ-1",
            "fields": {
                "summary": "Minimal issue",
            }
        }

        issue = JiraIssueMapper.to_entity(minimal_data, instance_id)

        assert issue.issue_key == "PROJ-1"
        assert issue.summary == "Minimal issue"
        assert issue.issue_type == "Task"  # Default
        assert issue.status == "To Do"  # Default
        assert issue.priority == "Medium"  # Default


class TestJiraProjectMapper:
    """Tests for JiraProjectMapper."""

    @pytest.fixture
    def jira_project_data(self):
        """Sample Jira project data."""
        return {
            "id": "10000",
            "key": "PROJ",
            "name": "Test Project",
            "description": "Test project description",
            "projectTypeKey": "software",
            "lead": {"accountId": "user123"},
            "avatarUrls": {"48x48": "https://example.com/avatar.png"},
            "self": "https://test.atlassian.net/rest/api/3/project/10000",
            "archived": False,
            "isPrivate": False,
        }

    def test_to_entity(self, jira_project_data):
        """Test converting Jira project to entity."""
        instance_id = uuid.uuid4()
        project = JiraProjectMapper.to_entity(jira_project_data, instance_id)

        assert isinstance(project, Project)
        assert project.instance_id == instance_id
        assert project.project_key == "PROJ"
        assert project.project_id == "10000"
        assert project.name == "Test Project"
        assert project.description == "Test project description"
        assert project.project_type == "software"
        assert project.lead_account_id == "user123"
        assert project.avatar_url == "https://example.com/avatar.png"
        assert project.is_archived is False
        assert project.is_private is False


class TestJiraUserMapper:
    """Tests for JiraUserMapper."""

    @pytest.fixture
    def jira_user_data(self):
        """Sample Jira user data."""
        return {
            "accountId": "user123",
            "accountType": "atlassian",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
            "avatarUrls": {"48x48": "https://example.com/avatar.png"},
            "active": True,
        }

    def test_to_entity(self, jira_user_data):
        """Test converting Jira user to entity."""
        instance_id = uuid.uuid4()
        user = JiraUserMapper.to_entity(jira_user_data, instance_id)

        assert isinstance(user, User)
        assert user.instance_id == instance_id
        assert user.account_id == "user123"
        assert user.account_type == "atlassian"
        assert user.display_name == "John Doe"
        assert user.email_address == "john@example.com"
        assert user.avatar_url == "https://example.com/avatar.png"
        assert user.is_active is True


class TestJiraCommentMapper:
    """Tests for JiraCommentMapper."""

    @pytest.fixture
    def jira_comment_data(self):
        """Sample Jira comment data."""
        return {
            "id": "10001",
            "body": "This is a test comment",
            "author": {"accountId": "user123"},
            "created": "2024-01-15T10:00:00.000Z",
            "updated": "2024-01-15T10:30:00.000Z",
        }

    def test_to_entity(self, jira_comment_data):
        """Test converting Jira comment to entity."""
        instance_id = uuid.uuid4()
        issue_key = "PROJ-123"

        comment = JiraCommentMapper.to_entity(
            jira_comment_data,
            instance_id,
            issue_key
        )

        assert isinstance(comment, Comment)
        assert comment.instance_id == instance_id
        assert comment.issue_key == issue_key
        assert comment.comment_id == "10001"
        assert comment.body == "This is a test comment"
        assert comment.body_format == "plain"
        assert comment.author_account_id == "user123"
        assert comment.is_public is True

    def test_to_entity_with_visibility(self):
        """Test converting comment with visibility restrictions."""
        instance_id = uuid.uuid4()
        issue_key = "PROJ-123"

        comment_data = {
            "id": "10001",
            "body": "Private comment",
            "author": {"accountId": "user123"},
            "visibility": {
                "type": "role",
                "value": "Administrators"
            },
            "created": "2024-01-15T10:00:00.000Z",
            "updated": "2024-01-15T10:00:00.000Z",
        }

        comment = JiraCommentMapper.to_entity(
            comment_data,
            instance_id,
            issue_key
        )

        assert comment.is_public is False
        assert comment.visibility_type == "role"
        assert comment.visibility_value == "Administrators"


class TestJiraChangelogMapper:
    """Tests for JiraChangelogMapper."""

    @pytest.fixture
    def jira_changelog_data(self):
        """Sample Jira changelog data."""
        return {
            "id": "10001",
            "author": {"accountId": "user123"},
            "created": "2024-01-15T10:00:00.000Z",
            "items": [
                {
                    "field": "status",
                    "fieldtype": "jira",
                    "from": "10000",
                    "fromString": "To Do",
                    "to": "10001",
                    "toString": "In Progress"
                },
                {
                    "field": "assignee",
                    "fieldtype": "jira",
                    "from": None,
                    "fromString": None,
                    "to": "user456",
                    "toString": "Jane Doe"
                }
            ]
        }

    def test_to_entity(self, jira_changelog_data):
        """Test converting Jira changelog to entity."""
        instance_id = uuid.uuid4()
        issue_key = "PROJ-123"

        changelog = JiraChangelogMapper.to_entity(
            jira_changelog_data,
            instance_id,
            issue_key
        )

        assert isinstance(changelog, Changelog)
        assert changelog.instance_id == instance_id
        assert changelog.issue_key == issue_key
        assert changelog.changelog_id == "10001"
        assert changelog.author_account_id == "user123"
        assert len(changelog.items) == 2
        assert changelog.items[0]["field"] == "status"
        assert changelog.items[0]["fromString"] == "To Do"
        assert changelog.items[0]["toString"] == "In Progress"
        assert changelog.items[1]["field"] == "assignee"

