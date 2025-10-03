"""Unit tests for MCP Jira tools."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.interfaces.mcp.jira.tools import (
    MCPContext,
    jira_search,
    jira_get_issue,
    jira_create_issue,
    jira_update_issue,
    jira_transition_issue,
)
from src.interfaces.mcp.jira.schemas import (
    JiraSearchParams,
    JiraGetIssueParams,
    JiraCreateIssueParams,
    JiraUpdateIssueParams,
    JiraTransitionIssueParams,
)
from src.interfaces.mcp.jira.errors import NotFoundError
from src.infrastructure.database.models.jira_instance import JiraInstance
from src.infrastructure.database.models.issue import Issue


@pytest.fixture
async def mock_context(db_session):
    """Create a mock MCP context."""
    tenant_id = uuid4()
    return MCPContext(
        session=db_session,
        tenant_id=tenant_id,
        user_id="test@example.com",
        request_id="test-request-123",
    )


@pytest.fixture
async def mock_instance(db_session, mock_context):
    """Create a mock Jira instance."""
    instance = JiraInstance(
        id=uuid4(),
        tenant_id=mock_context.tenant_id,
        base_url="https://test.atlassian.net",
        auth_type="api_token",
        is_active=True,
        sync_enabled=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(instance)
    await db_session.flush()
    return instance


@pytest.fixture
async def mock_issue(db_session, mock_context, mock_instance):
    """Create a mock issue."""
    issue = Issue(
        id=uuid4(),
        tenant_id=mock_context.tenant_id,
        instance_id=mock_instance.id,
        issue_key="TEST-123",
        issue_id="10001",
        summary="Test issue",
        description="Test description",
        issue_type="Task",
        status="Open",
        priority="Medium",
        custom_fields={},
        raw_jsonb={},
        jira_created_at=datetime.now(timezone.utc),
        jira_updated_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(issue)
    await db_session.flush()
    return issue


class TestJiraSearch:
    """Tests for jira.search tool."""

    async def test_search_returns_issues(self, mock_context, mock_instance, mock_issue):
        """Test that search returns issues."""
        params = JiraSearchParams(
            query="project = TEST",
            limit=10,
        )

        response = await jira_search(params, mock_context)

        assert response.total >= 1
        assert len(response.issues) >= 1
        assert response.instance_id == mock_instance.id
        assert response.query_time_ms >= 0

    async def test_search_with_instance_id(self, mock_context, mock_instance, mock_issue):
        """Test search with specific instance ID."""
        params = JiraSearchParams(
            query="project = TEST",
            instance_id=mock_instance.id,
            limit=10,
        )

        response = await jira_search(params, mock_context)

        assert response.instance_id == mock_instance.id

    async def test_search_with_invalid_instance(self, mock_context):
        """Test search with invalid instance ID."""
        params = JiraSearchParams(
            query="project = TEST",
            instance_id=uuid4(),  # Non-existent instance
            limit=10,
        )

        with pytest.raises(NotFoundError):
            await jira_search(params, mock_context)


class TestJiraGetIssue:
    """Tests for jira.get_issue tool."""

    async def test_get_issue_returns_details(self, mock_context, mock_instance, mock_issue):
        """Test that get_issue returns issue details."""
        params = JiraGetIssueParams(
            issue_key="TEST-123",
        )

        response = await jira_get_issue(params, mock_context)

        assert response.issue["key"] == "TEST-123"
        assert response.issue["summary"] == "Test issue"
        assert response.instance_id == mock_instance.id

    async def test_get_issue_not_found(self, mock_context, mock_instance):
        """Test get_issue with non-existent issue."""
        params = JiraGetIssueParams(
            issue_key="TEST-999",
        )

        with pytest.raises(NotFoundError):
            await jira_get_issue(params, mock_context)


class TestJiraCreateIssue:
    """Tests for jira.create_issue tool."""

    async def test_create_issue_success(self, mock_context, mock_instance):
        """Test successful issue creation."""
        params = JiraCreateIssueParams(
            instance_id=mock_instance.id,
            project_key="TEST",
            issue_type_id="10001",
            summary="New test issue",
        )

        response = await jira_create_issue(params, mock_context)

        assert response.issue["summary"] == "New test issue"
        assert response.instance_id == mock_instance.id
        assert response.audit_log_id is not None

    async def test_create_issue_with_idempotency(self, mock_context, mock_instance):
        """Test issue creation with idempotency key."""
        params = JiraCreateIssueParams(
            instance_id=mock_instance.id,
            project_key="TEST",
            issue_type_id="10001",
            summary="Idempotent issue",
            idempotency_key="test-key-123",
        )

        # First call
        response1 = await jira_create_issue(params, mock_context)
        await mock_context.session.commit()

        # Second call with same key should return same result
        response2 = await jira_create_issue(params, mock_context)

        assert response1.issue["key"] == response2.issue["key"]
        assert response1.audit_log_id == response2.audit_log_id


class TestJiraUpdateIssue:
    """Tests for jira.update_issue tool."""

    async def test_update_issue_success(self, mock_context, mock_instance, mock_issue):
        """Test successful issue update."""
        params = JiraUpdateIssueParams(
            issue_key="TEST-123",
            fields={"summary": "Updated summary"},
        )

        response = await jira_update_issue(params, mock_context)

        assert response["success"] is True
        assert response["issue_key"] == "TEST-123"
        assert "summary" in response["updated_fields"]


class TestJiraTransitionIssue:
    """Tests for jira.transition_issue tool."""

    async def test_transition_issue_success(self, mock_context, mock_instance, mock_issue):
        """Test successful issue transition."""
        params = JiraTransitionIssueParams(
            issue_key="TEST-123",
            to_status="In Progress",
        )

        response = await jira_transition_issue(params, mock_context)

        assert response["success"] is True
        assert response["from_status"] == "Open"
        assert response["to_status"] == "In Progress"

    async def test_transition_with_comment(self, mock_context, mock_instance, mock_issue):
        """Test transition with comment."""
        params = JiraTransitionIssueParams(
            issue_key="TEST-123",
            to_status="Done",
            comment="Completed the work",
        )

        response = await jira_transition_issue(params, mock_context)

        assert response["success"] is True
        assert response["to_status"] == "Done"

