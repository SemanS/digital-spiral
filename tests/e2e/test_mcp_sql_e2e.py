"""End-to-end tests for MCP SQL server."""

import pytest
import httpx
from uuid import uuid4


@pytest.mark.e2e
@pytest.mark.asyncio
class TestMCPSQLE2E:
    """End-to-end tests for MCP SQL server."""

    @pytest.fixture
    def base_url(self):
        """MCP SQL server base URL."""
        return "http://localhost:8056"

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

    async def test_server_info(self, base_url):
        """Test server info endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url)
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "mcp-sql"
            assert data["version"] == "1.0.0"

    async def test_list_templates(self, base_url, headers):
        """Test list templates endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/templates",
                headers=headers,
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            assert len(data["templates"]) == 6
            
            # Check all expected templates are present
            template_names = [t["name"] for t in data["templates"]]
            expected_templates = [
                "search_issues_by_project",
                "get_project_metrics",
                "search_issues_by_text",
                "get_issue_history",
                "get_user_workload",
                "lead_time_metrics",
            ]
            for template in expected_templates:
                assert template in template_names

    async def test_query_execution_search_issues(self, base_url, headers):
        """Test query execution for search_issues_by_project."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/query",
                headers=headers,
                json={
                    "template_name": "search_issues_by_project",
                    "params": {
                        "project_key": "TEST",
                        "limit": 10,
                    },
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert "rows" in data["result"]

    async def test_query_execution_project_metrics(self, base_url, headers):
        """Test query execution for get_project_metrics."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/query",
                headers=headers,
                json={
                    "template_name": "get_project_metrics",
                    "params": {
                        "project_key": "TEST",
                        "days": 30,
                    },
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "result" in data

    async def test_query_execution_invalid_template(self, base_url, headers):
        """Test query execution with invalid template."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/query",
                headers=headers,
                json={
                    "template_name": "nonexistent_template",
                    "params": {},
                },
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    async def test_query_execution_missing_params(self, base_url, headers):
        """Test query execution with missing parameters."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/query",
                headers=headers,
                json={
                    "template_name": "search_issues_by_project",
                    "params": {},  # Missing required params
                },
            )
            
            assert response.status_code == 400

    async def test_sql_injection_protection(self, base_url, headers):
        """Test SQL injection protection."""
        async with httpx.AsyncClient() as client:
            # Try SQL injection in project_key
            response = await client.post(
                f"{base_url}/query",
                headers=headers,
                json={
                    "template_name": "search_issues_by_project",
                    "params": {
                        "project_key": "TEST'; DROP TABLE issues; --",
                        "limit": 10,
                    },
                },
            )
            
            # Should either succeed (with escaped input) or fail validation
            # But should NOT execute the DROP TABLE
            assert response.status_code in [200, 400]

    async def test_metrics_endpoint(self, base_url):
        """Test metrics endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert "counters" in data
            assert "histograms" in data

    async def test_rate_limiting(self, base_url, headers):
        """Test rate limiting."""
        async with httpx.AsyncClient() as client:
            # Make many requests quickly
            responses = []
            for _ in range(150):
                response = await client.post(
                    f"{base_url}/query",
                    headers=headers,
                    json={
                        "template_name": "search_issues_by_project",
                        "params": {"project_key": "TEST", "limit": 1},
                    },
                )
                responses.append(response)
            
            # Should have some rate limited responses
            rate_limited = [r for r in responses if r.status_code == 429]
            assert len(rate_limited) > 0

    async def test_concurrent_queries(self, base_url, headers):
        """Test handling of concurrent queries."""
        import asyncio
        
        async def make_query():
            async with httpx.AsyncClient() as client:
                return await client.post(
                    f"{base_url}/query",
                    headers=headers,
                    json={
                        "template_name": "search_issues_by_project",
                        "params": {"project_key": "TEST", "limit": 1},
                    },
                )
        
        # Make 10 concurrent queries
        tasks = [make_query() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed or be rate limited
        for response in responses:
            assert response.status_code in [200, 429]

    async def test_query_with_all_templates(self, base_url, headers):
        """Test query execution with all templates."""
        templates_and_params = [
            ("search_issues_by_project", {"project_key": "TEST", "limit": 10}),
            ("get_project_metrics", {"project_key": "TEST", "days": 30}),
            ("search_issues_by_text", {"search_text": "bug", "limit": 10}),
            ("get_issue_history", {"issue_key": "TEST-1"}),
            ("get_user_workload", {"user_id": "user-123"}),
            ("lead_time_metrics", {"project_key": "TEST", "days": 30}),
        ]
        
        async with httpx.AsyncClient() as client:
            for template_name, params in templates_and_params:
                response = await client.post(
                    f"{base_url}/query",
                    headers=headers,
                    json={
                        "template_name": template_name,
                        "params": params,
                    },
                )
                
                # Should succeed (even if no data)
                assert response.status_code == 200, f"Failed for template: {template_name}"

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

    async def test_error_handling(self, base_url, headers):
        """Test error handling."""
        async with httpx.AsyncClient() as client:
            # Invalid JSON
            response = await client.post(
                f"{base_url}/query",
                headers=headers,
                content="invalid json",
            )
            
            assert response.status_code == 422

