"""End-to-end tests for MCP Jira server."""

import pytest
import httpx
from uuid import uuid4


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPJiraE2E:
    """End-to-end tests for MCP Jira server."""

    @pytest.fixture
    def base_url(self):
        """MCP Jira server base URL."""
        return "http://localhost:8055"

    @pytest.fixture
    def headers(self):
        """Request headers."""
        return {
            "X-Tenant-ID": str(uuid4()),
            "X-User-ID": "test-user",
            "Content-Type": "application/json",
        }

    async def test_health_check(self, base_url):
        """Test health check endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data

    async def test_server_info(self, base_url):
        """Test server info endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "mcp-jira"
            assert data["version"] == "1.0.0"
            assert "tools" in data

    async def test_list_tools(self, base_url, headers):
        """Test list tools endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/tools",
                headers=headers,
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "tools" in data
            assert len(data["tools"]) == 8
            
            # Check all expected tools are present
            tool_names = [tool["name"] for tool in data["tools"]]
            expected_tools = [
                "jira.search",
                "jira.get_issue",
                "jira.create_issue",
                "jira.update_issue",
                "jira.transition_issue",
                "jira.add_comment",
                "jira.link_issues",
                "jira.list_transitions",
            ]
            for tool in expected_tools:
                assert tool in tool_names

    async def test_metrics_endpoint(self, base_url):
        """Test metrics endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert "counters" in data
            assert "histograms" in data
            assert "gauges" in data

    async def test_tool_invocation_search(self, base_url, headers):
        """Test jira.search tool invocation."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/tools/invoke",
                headers=headers,
                json={
                    "name": "jira.search",
                    "arguments": {
                        "query": "project = TEST",
                        "limit": 10,
                    },
                },
            )
            
            # Should return 200 even if no issues found
            assert response.status_code == 200
            data = response.json()
            assert "result" in data

    async def test_tool_invocation_invalid_tool(self, base_url, headers):
        """Test invocation of non-existent tool."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/tools/invoke",
                headers=headers,
                json={
                    "name": "jira.nonexistent",
                    "arguments": {},
                },
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    async def test_tool_invocation_missing_arguments(self, base_url, headers):
        """Test tool invocation with missing arguments."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/tools/invoke",
                headers=headers,
                json={
                    "name": "jira.search",
                    "arguments": {},  # Missing required 'query'
                },
            )
            
            assert response.status_code == 400

    async def test_rate_limiting(self, base_url, headers):
        """Test rate limiting."""
        async with httpx.AsyncClient() as client:
            # Make many requests quickly
            responses = []
            for _ in range(150):  # Exceed default limit of 100
                response = await client.post(
                    f"{base_url}/tools/invoke",
                    headers=headers,
                    json={
                        "name": "jira.search",
                        "arguments": {"query": "project = TEST", "limit": 1},
                    },
                )
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited = [r for r in responses if r.status_code == 429]
            assert len(rate_limited) > 0

    async def test_idempotency(self, base_url, headers):
        """Test idempotency with same idempotency key."""
        idempotency_key = str(uuid4())
        headers_with_key = {
            **headers,
            "X-Idempotency-Key": idempotency_key,
        }
        
        async with httpx.AsyncClient() as client:
            # First request
            response1 = await client.post(
                f"{base_url}/tools/invoke",
                headers=headers_with_key,
                json={
                    "name": "jira.search",
                    "arguments": {"query": "project = TEST", "limit": 1},
                },
            )
            
            # Second request with same key
            response2 = await client.post(
                f"{base_url}/tools/invoke",
                headers=headers_with_key,
                json={
                    "name": "jira.search",
                    "arguments": {"query": "project = TEST", "limit": 1},
                },
            )
            
            # Both should succeed
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            # Results should be identical
            assert response1.json() == response2.json()

    async def test_sse_connection(self, base_url, headers):
        """Test SSE connection."""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "GET",
                f"{base_url}/sse",
                headers=headers,
            ) as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")
                
                # Read first event (should be heartbeat or connection)
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        # Got an event
                        break

    async def test_concurrent_requests(self, base_url, headers):
        """Test handling of concurrent requests."""
        import asyncio
        
        async def make_request():
            async with httpx.AsyncClient() as client:
                return await client.post(
                    f"{base_url}/tools/invoke",
                    headers=headers,
                    json={
                        "name": "jira.search",
                        "arguments": {"query": "project = TEST", "limit": 1},
                    },
                )
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code in [200, 429]  # OK or rate limited

    async def test_error_handling(self, base_url, headers):
        """Test error handling."""
        async with httpx.AsyncClient() as client:
            # Invalid JSON
            response = await client.post(
                f"{base_url}/tools/invoke",
                headers=headers,
                content="invalid json",
            )
            
            assert response.status_code == 422  # Unprocessable entity

    async def test_missing_headers(self, base_url):
        """Test request without required headers."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/tools/invoke",
                json={
                    "name": "jira.search",
                    "arguments": {"query": "project = TEST"},
                },
            )
            
            # Should fail without tenant ID
            assert response.status_code in [400, 422]

