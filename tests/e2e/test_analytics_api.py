"""E2E tests for Analytics API endpoints."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.asyncio
class TestAnalyticsAPIE2E:
    """E2E tests for Analytics API."""
    
    async def test_execute_analytics_query(self, async_client: AsyncClient):
        """Test POST /analytics/query endpoint."""
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "total_issues",
                    "aggregation": "count",
                }
            ],
        }
        
        response = await async_client.post(
            "/analytics/query",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "metadata" in data
        assert "row_count" in data["metadata"]
        assert "execution_time_ms" in data["metadata"]
    
    async def test_execute_query_with_invalid_spec(self, async_client: AsyncClient):
        """Test query with invalid spec returns 400."""
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "invalid",
                    "aggregation": "avg",
                    "field": "invalid_field_xyz",
                }
            ],
        }
        
        response = await async_client.post(
            "/analytics/query",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data["detail"]
    
    async def test_validate_analytics_spec(self, async_client: AsyncClient):
        """Test POST /analytics/query/validate endpoint."""
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "total",
                    "aggregation": "count",
                }
            ],
        }
        
        response = await async_client.post(
            "/analytics/query/validate",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert data["is_valid"] == True
    
    async def test_get_available_metrics(self, async_client: AsyncClient):
        """Test GET /analytics/metrics endpoint."""
        response = await async_client.get(
            "/analytics/metrics",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "metrics" in data
        assert "count" in data
        assert isinstance(data["metrics"], list)
    
    async def test_get_metrics_with_category_filter(self, async_client: AsyncClient):
        """Test GET /analytics/metrics with category filter."""
        response = await async_client.get(
            "/analytics/metrics?category=velocity",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "metrics" in data
        # All metrics should be in velocity category
        for metric in data["metrics"]:
            assert metric.get("category") == "velocity"
    
    async def test_search_metrics(self, async_client: AsyncClient):
        """Test GET /analytics/metrics/search endpoint."""
        response = await async_client.get(
            "/analytics/metrics/search?q=velocity&limit=5",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "metrics" in data
        assert "count" in data
        assert "query" in data
        assert data["query"] == "velocity"
        assert len(data["metrics"]) <= 5
    
    async def test_get_cache_stats(self, async_client: AsyncClient):
        """Test GET /analytics/cache/stats endpoint."""
        response = await async_client.get(
            "/analytics/cache/stats",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_entries" in data
        assert "active_entries" in data
        assert "expired_entries" in data
    
    async def test_invalidate_cache(self, async_client: AsyncClient):
        """Test POST /analytics/cache/invalidate endpoint."""
        # First, execute a query to create cache
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "total",
                    "aggregation": "count",
                }
            ],
        }
        
        await async_client.post(
            "/analytics/query",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        # Invalidate cache
        response = await async_client.post(
            "/analytics/cache/invalidate",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "invalidated_count" in data
        assert "scope" in data
    
    async def test_cleanup_expired_cache(self, async_client: AsyncClient):
        """Test POST /analytics/cache/cleanup endpoint."""
        response = await async_client.post(
            "/analytics/cache/cleanup",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "removed_count" in data
    
    async def test_query_with_filters(self, async_client: AsyncClient):
        """Test query with filters."""
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "done_count",
                    "aggregation": "count",
                }
            ],
            "filters": [
                {
                    "field": "status",
                    "operator": "eq",
                    "value": "Done",
                }
            ],
        }
        
        response = await async_client.post(
            "/analytics/query",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    async def test_query_with_grouping(self, async_client: AsyncClient):
        """Test query with grouping."""
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "count_by_status",
                    "aggregation": "count",
                }
            ],
            "group_by": [
                {
                    "field": "status",
                }
            ],
            "sort_by": [
                {
                    "field": "count_by_status",
                    "direction": "desc",
                }
            ],
        }
        
        response = await async_client.post(
            "/analytics/query",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
    
    async def test_query_with_date_range(self, async_client: AsyncClient):
        """Test query with date range."""
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "recent_issues",
                    "aggregation": "count",
                }
            ],
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
        }
        
        response = await async_client.post(
            "/analytics/query",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    async def test_query_with_limit(self, async_client: AsyncClient):
        """Test query with limit."""
        spec = {
            "entity": "issues",
            "metrics": [
                {
                    "name": "count",
                    "aggregation": "count",
                }
            ],
            "group_by": [
                {
                    "field": "status",
                }
            ],
            "limit": 3,
        }
        
        response = await async_client.post(
            "/analytics/query",
            json=spec,
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) <= 3

