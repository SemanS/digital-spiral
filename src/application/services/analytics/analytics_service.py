"""Main Analytics Service orchestrating all analytics operations."""

from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.schemas.analytics_spec import AnalyticsSpec
from .analytics_executor import AnalyticsExecutor
from .cache_service import CacheService
from .metrics_catalog_service import MetricsCatalogService


class AnalyticsService:
    """Main analytics service orchestrating query execution and caching."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        """Initialize analytics service.
        
        Args:
            session: Database session
            tenant_id: Tenant ID
        """
        self.session = session
        self.tenant_id = tenant_id
        
        # Initialize sub-services
        self.executor = AnalyticsExecutor(session, tenant_id)
        self.cache = CacheService(session, tenant_id)
        self.metrics_catalog = MetricsCatalogService(session)
    
    async def execute_analytics_spec(
        self,
        spec: AnalyticsSpec,
        use_cache: bool = True,
        cache_ttl_hours: int = 24,
    ) -> Dict[str, Any]:
        """Execute analytics specification with caching.
        
        Args:
            spec: Analytics specification
            use_cache: Whether to use cache (default: True)
            cache_ttl_hours: Cache TTL in hours (default: 24)
            
        Returns:
            Dictionary with results and metadata
        """
        # Try to get from cache
        if use_cache:
            cached_result = await self.cache.get_cached_result(spec)
            if cached_result:
                return cached_result
        
        # Execute query
        result = await self.executor.execute_spec(spec)
        
        # Cache result
        if use_cache:
            await self.cache.cache_result(
                spec=spec,
                sql_query=result["metadata"]["sql_query"],
                result_data=result["data"],
                row_count=result["metadata"]["row_count"],
                execution_time_ms=result["metadata"]["execution_time_ms"],
                ttl_hours=cache_ttl_hours,
            )
            result["metadata"]["cached"] = False
        
        return result
    
    async def execute_metric(
        self,
        metric_name: str,
        parameters: Dict[str, Any],
        use_cache: bool = True,
        cache_ttl_hours: int = 24,
    ) -> Dict[str, Any]:
        """Execute predefined metric with caching.
        
        Args:
            metric_name: Metric name
            parameters: Metric parameters
            use_cache: Whether to use cache (default: True)
            cache_ttl_hours: Cache TTL in hours (default: 24)
            
        Returns:
            Dictionary with results and metadata
            
        Raises:
            ValueError: If metric not found or parameters invalid
        """
        # Get metric from catalog
        metric = await self.metrics_catalog.get_metric(self.tenant_id, metric_name)
        if not metric:
            raise ValueError(f"Metric '{metric_name}' not found")
        
        if not metric.is_active:
            raise ValueError(f"Metric '{metric_name}' is not active")
        
        # Validate parameters
        is_valid, error = metric.validate_parameters(parameters)
        if not is_valid:
            raise ValueError(f"Invalid parameters: {error}")
        
        # Execute metric
        result = await self.executor.execute_metric(
            metric_name=metric_name,
            parameters=parameters,
            sql_template=metric.sql_template,
        )
        
        return result
    
    async def get_available_metrics(
        self,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> list[Dict[str, Any]]:
        """Get available metrics for tenant.
        
        Args:
            category: Filter by category (optional)
            tags: Filter by tags (optional)
            
        Returns:
            List of metric definitions
        """
        metrics = await self.metrics_catalog.get_all_metrics(
            tenant_id=self.tenant_id,
            category=category,
            is_active=True,
            tags=tags,
        )
        
        return [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "category": m.category,
                "parameters": m.parameter_names,
                "required_parameters": m.required_parameters,
                "unit": m.unit,
                "tags": m.tags,
            }
            for m in metrics
        ]
    
    async def search_metrics(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Dict[str, Any]]:
        """Search metrics by name or description.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching metrics
        """
        metrics = await self.metrics_catalog.search_metrics(
            tenant_id=self.tenant_id,
            query=query,
            limit=limit,
        )
        
        return [
            {
                "name": m.name,
                "display_name": m.display_name,
                "description": m.description,
                "category": m.category,
                "unit": m.unit,
            }
            for m in metrics
        ]
    
    async def validate_spec(self, spec: AnalyticsSpec) -> Dict[str, Any]:
        """Validate analytics specification.
        
        Args:
            spec: Analytics specification
            
        Returns:
            Validation results
        """
        # Build query
        sql_query, params = self.executor.query_builder.build_query(spec)
        
        # Validate query
        validation = await self.executor.validate_query(sql_query)
        
        return {
            "is_valid": validation["is_valid"],
            "is_safe": validation["is_safe"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "sql_query": sql_query if validation["is_valid"] else None,
        }
    
    async def estimate_query_cost(self, spec: AnalyticsSpec) -> Dict[str, Any]:
        """Estimate query execution cost.
        
        Args:
            spec: Analytics specification
            
        Returns:
            Cost estimates
        """
        # Build query
        sql_query, params = self.executor.query_builder.build_query(spec)
        
        # Get cost estimate
        cost = await self.executor.estimate_query_cost(sql_query, params)
        
        return {
            "total_cost": cost.get("total_cost"),
            "startup_cost": cost.get("startup_cost"),
            "estimated_rows": cost.get("plan_rows"),
            "sql_query": sql_query,
        }
    
    async def invalidate_cache(self, spec: Optional[AnalyticsSpec] = None) -> Dict[str, Any]:
        """Invalidate cache.
        
        Args:
            spec: Specific spec to invalidate (optional, if None invalidates all)
            
        Returns:
            Invalidation results
        """
        if spec:
            invalidated = await self.cache.invalidate_cache(spec)
            return {
                "invalidated_count": 1 if invalidated else 0,
                "scope": "specific",
            }
        else:
            count = await self.cache.invalidate_all_cache()
            return {
                "invalidated_count": count,
                "scope": "all",
            }
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return await self.cache.get_cache_stats()
    
    async def cleanup_expired_cache(self) -> Dict[str, Any]:
        """Clean up expired cache entries.
        
        Returns:
            Cleanup results
        """
        count = await self.cache.cleanup_expired_cache()
        return {
            "removed_count": count,
        }

