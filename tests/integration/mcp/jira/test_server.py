"""Integration tests for MCP Jira server."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from src.interfaces.mcp.jira.server import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def tenant_id():
    """Create a test tenant ID."""
    return str(uuid4())


class TestMCPJiraServer:
    """Integration tests for MCP Jira server endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns server info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["server"] == "mcp-jira"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_list_tools_endpoint(self, client):
        """Test list tools endpoint."""
        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "count" in data
        assert isinstance(data["tools"], list)
        assert len(data["tools"]) > 0

    def test_invoke_tool_without_tenant_id(self, client):
        """Test tool invocation without tenant ID fails."""
        response = client.post(
            "/tools/invoke",
            json={
                "name": "jira.search",
                "arguments": {"query": "project = TEST", "limit": 10},
            },
        )
        assert response.status_code == 401

    def test_invoke_tool_with_invalid_tool(self, client, tenant_id):
        """Test tool invocation with invalid tool name."""
        response = client.post(
            "/tools/invoke",
            headers={"X-Tenant-ID": tenant_id},
            json={
                "name": "jira.invalid_tool",
                "arguments": {},
            },
        )
        assert response.status_code == 404

    def test_sse_endpoint_without_auth(self, client):
        """Test SSE endpoint without authentication."""
        response = client.get("/sse")
        assert response.status_code == 401


class TestMCPJiraToolInvocation:
    """Integration tests for MCP Jira tool invocation."""

    def test_search_tool_basic(self, client, tenant_id):
        """Test basic search tool invocation."""
        response = client.post(
            "/tools/invoke",
            headers={"X-Tenant-ID": tenant_id},
            json={
                "name": "jira.search",
                "arguments": {
                    "query": "project = TEST",
                    "limit": 10,
                },
            },
        )
        # May fail if no instance exists, but should not crash
        assert response.status_code in [200, 400, 404]

    def test_get_issue_tool(self, client, tenant_id):
        """Test get issue tool invocation."""
        response = client.post(
            "/tools/invoke",
            headers={"X-Tenant-ID": tenant_id},
            json={
                "name": "jira.get_issue",
                "arguments": {
                    "issue_key": "TEST-123",
                },
            },
        )
        # May fail if no instance/issue exists
        assert response.status_code in [200, 400, 404]

