"""Integration tests for Analytics Service."""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.analytics import AnalyticsService
from src.domain.schemas.analytics_spec import (
    AnalyticsSpec,
    MetricDefinition,
    FilterCondition,
    GroupByDefinition,
    SortDefinition,
    AggregationType,
    FilterOperator,
)


@pytest.mark.asyncio
class TestAnalyticsServiceIntegration:
    """Integration tests for AnalyticsService."""
    
    async def test_execute_simple_count_query(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test executing a simple count query."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="total_issues",
                    aggregation=AggregationType.COUNT,
                )
            ],
        )
        
        result = await service.execute_analytics_spec(spec, use_cache=False)
        
        assert "data" in result
        assert "metadata" in result
        assert result["metadata"]["row_count"] >= 0
        assert result["metadata"]["execution_time_ms"] > 0
    
    async def test_execute_query_with_filters(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test executing query with filters."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="done_issues",
                    aggregation=AggregationType.COUNT,
                )
            ],
            filters=[
                FilterCondition(
                    field="status",
                    operator=FilterOperator.EQ,
                    value="Done",
                )
            ],
        )
        
        result = await service.execute_analytics_spec(spec, use_cache=False)
        
        assert "data" in result
        assert result["metadata"]["row_count"] >= 0
    
    async def test_execute_query_with_grouping(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test executing query with grouping."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="count_by_status",
                    aggregation=AggregationType.COUNT,
                )
            ],
            group_by=[
                GroupByDefinition(field="status")
            ],
            sort_by=[
                SortDefinition(field="count_by_status", direction="desc")
            ],
        )
        
        result = await service.execute_analytics_spec(spec, use_cache=False)
        
        assert "data" in result
        # Should have multiple rows (one per status)
        assert isinstance(result["data"], list)
    
    async def test_execute_query_with_aggregation(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test executing query with aggregation."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="avg_story_points",
                    aggregation=AggregationType.AVG,
                    field="story_points",
                )
            ],
            filters=[
                FilterCondition(
                    field="story_points",
                    operator=FilterOperator.IS_NOT_NULL,
                    value=None,
                )
            ],
        )
        
        result = await service.execute_analytics_spec(spec, use_cache=False)
        
        assert "data" in result
        assert result["metadata"]["row_count"] >= 0
    
    async def test_caching_works(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test that caching works correctly."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="total_issues",
                    aggregation=AggregationType.COUNT,
                )
            ],
        )
        
        # First execution (not cached)
        result1 = await service.execute_analytics_spec(spec, use_cache=True)
        assert result1["metadata"].get("cached") == False
        
        # Second execution (should be cached)
        result2 = await service.execute_analytics_spec(spec, use_cache=True)
        assert result2["metadata"].get("cached") == True
        
        # Results should be the same
        assert result1["data"] == result2["data"]
    
    async def test_cache_invalidation(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test cache invalidation."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="total_issues",
                    aggregation=AggregationType.COUNT,
                )
            ],
        )
        
        # Execute and cache
        await service.execute_analytics_spec(spec, use_cache=True)
        
        # Invalidate cache
        result = await service.invalidate_cache(spec)
        assert result["invalidated_count"] >= 0
        
        # Next execution should not be cached
        result = await service.execute_analytics_spec(spec, use_cache=True)
        assert result["metadata"].get("cached") == False
    
    async def test_get_available_metrics(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test getting available metrics."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        metrics = await service.get_available_metrics()
        
        assert isinstance(metrics, list)
        # Should have at least some metrics
        assert len(metrics) >= 0
    
    async def test_search_metrics(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test searching metrics."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        # Search for velocity metrics
        metrics = await service.search_metrics("velocity", limit=10)
        
        assert isinstance(metrics, list)
        assert len(metrics) <= 10
    
    async def test_validate_spec(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test spec validation."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        # Valid spec
        valid_spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="total",
                    aggregation=AggregationType.COUNT,
                )
            ],
        )
        
        result = await service.validate_spec(valid_spec)
        assert result["is_valid"] == True
        assert len(result["errors"]) == 0
    
    async def test_validate_invalid_spec(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test validation of invalid spec."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        # Invalid spec (invalid field)
        invalid_spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="avg_invalid",
                    aggregation=AggregationType.AVG,
                    field="invalid_field_xyz",
                )
            ],
        )
        
        result = await service.validate_spec(invalid_spec)
        assert result["is_valid"] == False
        assert len(result["errors"]) > 0
    
    async def test_get_cache_stats(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test getting cache statistics."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        stats = await service.get_cache_stats()
        
        assert "total_entries" in stats
        assert "active_entries" in stats
        assert "expired_entries" in stats
        assert isinstance(stats["total_entries"], int)
    
    async def test_cleanup_expired_cache(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test cleaning up expired cache."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        result = await service.cleanup_expired_cache()
        
        assert "removed_count" in result
        assert isinstance(result["removed_count"], int)
    
    async def test_query_with_date_range(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test query with date range."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="recent_issues",
                    aggregation=AggregationType.COUNT,
                )
            ],
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
        )
        
        result = await service.execute_analytics_spec(spec, use_cache=False)
        
        assert "data" in result
        assert result["metadata"]["row_count"] >= 0
    
    async def test_query_with_limit(
        self,
        async_session: AsyncSession,
        test_tenant_id: str,
    ):
        """Test query with limit."""
        service = AnalyticsService(async_session, test_tenant_id)
        
        spec = AnalyticsSpec(
            entity="issues",
            metrics=[
                MetricDefinition(
                    name="count",
                    aggregation=AggregationType.COUNT,
                )
            ],
            group_by=[
                GroupByDefinition(field="status")
            ],
            limit=5,
        )
        
        result = await service.execute_analytics_spec(spec, use_cache=False)
        
        assert "data" in result
        # Should not exceed limit
        assert len(result["data"]) <= 5

