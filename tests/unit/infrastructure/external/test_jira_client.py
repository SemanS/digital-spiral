"""Unit tests for Jira API client."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, Response
from unittest.mock import AsyncMock, MagicMock, patch

from src.infrastructure.external.jira import (
    JiraAPIError,
    JiraAuthenticationError,
    JiraClient,
    JiraNotFoundError,
    JiraRateLimitError,
)


@pytest.fixture
def jira_client():
    """Create Jira client for testing."""
    return JiraClient(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test-token",
    )


@pytest.fixture
def jira_client_oauth():
    """Create Jira client with OAuth for testing."""
    return JiraClient(
        base_url="https://test.atlassian.net",
        access_token="test-access-token",
    )


class TestJiraClientInit:
    """Tests for JiraClient initialization."""

    def test_init_with_basic_auth(self):
        """Test initialization with basic auth."""
        client = JiraClient(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        )

        assert client.base_url == "https://test.atlassian.net"
        assert client.auth == ("test@example.com", "test-token")

    def test_init_with_oauth(self):
        """Test initialization with OAuth."""
        client = JiraClient(
            base_url="https://test.atlassian.net",
            access_token="test-access-token",
        )

        assert client.base_url == "https://test.atlassian.net"
        assert client.auth is None
        assert "Bearer test-access-token" in client.headers["Authorization"]

    def test_init_without_credentials(self):
        """Test initialization without credentials raises error."""
        with pytest.raises(ValueError):
            JiraClient(base_url="https://test.atlassian.net")

    def test_base_url_trailing_slash(self):
        """Test that trailing slash is removed from base URL."""
        client = JiraClient(
            base_url="https://test.atlassian.net/",
            email="test@example.com",
            api_token="test-token",
        )

        assert client.base_url == "https://test.atlassian.net"


class TestJiraClientRequests:
    """Tests for JiraClient HTTP requests."""

    @pytest.mark.asyncio
    async def test_make_url(self, jira_client):
        """Test URL construction."""
        url = jira_client._make_url("/rest/api/3/issue/PROJ-123")
        assert url == "https://test.atlassian.net/rest/api/3/issue/PROJ-123"

        # Test without leading slash
        url = jira_client._make_url("rest/api/3/issue/PROJ-123")
        assert url == "https://test.atlassian.net/rest/api/3/issue/PROJ-123"

    @pytest.mark.asyncio
    async def test_get_request_success(self, jira_client):
        """Test successful GET request."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "PROJ-123", "summary": "Test issue"}

        with patch.object(jira_client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await jira_client.get("/rest/api/3/issue/PROJ-123")

            assert result == {"key": "PROJ-123", "summary": "Test issue"}
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_request_success(self, jira_client):
        """Test successful POST request."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "10001", "key": "PROJ-123"}

        with patch.object(jira_client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await jira_client.post(
                "/rest/api/3/issue",
                json={"fields": {"summary": "Test"}}
            )

            assert result == {"id": "10001", "key": "PROJ-123"}

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, jira_client):
        """Test rate limit error handling."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        with patch.object(jira_client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(JiraRateLimitError) as exc_info:
                await jira_client.get("/rest/api/3/issue/PROJ-123")

            assert exc_info.value.status_code == 429
            assert "60" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authentication_error(self, jira_client):
        """Test authentication error handling."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 401

        with patch.object(jira_client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(JiraAuthenticationError) as exc_info:
                await jira_client.get("/rest/api/3/issue/PROJ-123")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_not_found_error(self, jira_client):
        """Test not found error handling."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 404

        with patch.object(jira_client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(JiraNotFoundError) as exc_info:
                await jira_client.get("/rest/api/3/issue/PROJ-999")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_generic_api_error(self, jira_client):
        """Test generic API error handling."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.return_value = {"errorMessages": ["Server error"]}

        with patch.object(jira_client.client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with pytest.raises(JiraAPIError) as exc_info:
                await jira_client.get("/rest/api/3/issue/PROJ-123")

            assert exc_info.value.status_code == 500


class TestJiraClientConvenienceMethods:
    """Tests for Jira client convenience methods."""

    @pytest.mark.asyncio
    async def test_get_myself(self, jira_client):
        """Test get_myself method."""
        expected = {
            "accountId": "123",
            "displayName": "Test User",
            "emailAddress": "test@example.com"
        }

        with patch.object(jira_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected

            result = await jira_client.get_myself()

            assert result == expected
            mock_get.assert_called_once_with("/rest/api/3/myself")

    @pytest.mark.asyncio
    async def test_get_issue(self, jira_client):
        """Test get_issue method."""
        expected = {"key": "PROJ-123", "fields": {"summary": "Test"}}

        with patch.object(jira_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected

            result = await jira_client.get_issue("PROJ-123")

            assert result == expected
            mock_get.assert_called_once_with("/rest/api/3/issue/PROJ-123", params={})

    @pytest.mark.asyncio
    async def test_get_issue_with_expand(self, jira_client):
        """Test get_issue with expand parameter."""
        expected = {"key": "PROJ-123", "changelog": {}}

        with patch.object(jira_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected

            result = await jira_client.get_issue("PROJ-123", expand=["changelog"])

            assert result == expected
            mock_get.assert_called_once_with(
                "/rest/api/3/issue/PROJ-123",
                params={"expand": "changelog"}
            )

    @pytest.mark.asyncio
    async def test_search_issues(self, jira_client):
        """Test search_issues method."""
        expected = {
            "total": 1,
            "issues": [{"key": "PROJ-123"}]
        }

        with patch.object(jira_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected

            result = await jira_client.search_issues("project = PROJ")

            assert result == expected
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_project(self, jira_client):
        """Test get_project method."""
        expected = {"key": "PROJ", "name": "Test Project"}

        with patch.object(jira_client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = expected

            result = await jira_client.get_project("PROJ")

            assert result == expected
            mock_get.assert_called_once_with("/rest/api/3/project/PROJ", params={})


class TestJiraClientContextManager:
    """Tests for Jira client context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with JiraClient(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="test-token",
        ) as client:
            assert client is not None
            assert isinstance(client, JiraClient)

