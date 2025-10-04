"""Metrics Catalog Service for managing predefined metrics."""

from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import MetricsCatalog


class MetricsCatalogService:
    """Service for CRUD operations on metrics catalog."""
    
    def __init__(self, session: AsyncSession):
        """Initialize service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def get_all_metrics(
        self,
        tenant_id: UUID,
        category: Optional[str] = None,
        is_active: Optional[bool] = True,
        tags: Optional[List[str]] = None,
    ) -> List[MetricsCatalog]:
        """Get all metrics for a tenant.
        
        Args:
            tenant_id: Tenant ID
            category: Filter by category (optional)
            is_active: Filter by active status (default: True)
            tags: Filter by tags (optional)
            
        Returns:
            List of metrics
        """
        query = select(MetricsCatalog).where(
            MetricsCatalog.tenant_id == tenant_id
        )
        
        if category:
            query = query.where(MetricsCatalog.category == category)
        
        if is_active is not None:
            query = query.where(MetricsCatalog.is_active == is_active)
        
        if tags:
            # Filter by tags (PostgreSQL array contains)
            for tag in tags:
                query = query.where(MetricsCatalog.tags.contains([tag]))
        
        query = query.order_by(MetricsCatalog.category, MetricsCatalog.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_metric(
        self,
        tenant_id: UUID,
        metric_name: str,
    ) -> Optional[MetricsCatalog]:
        """Get a specific metric by name.
        
        Args:
            tenant_id: Tenant ID
            metric_name: Metric name
            
        Returns:
            Metric or None if not found
        """
        query = select(MetricsCatalog).where(
            and_(
                MetricsCatalog.tenant_id == tenant_id,
                MetricsCatalog.name == metric_name,
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_metric_by_id(
        self,
        tenant_id: UUID,
        metric_id: UUID,
    ) -> Optional[MetricsCatalog]:
        """Get a specific metric by ID.
        
        Args:
            tenant_id: Tenant ID
            metric_id: Metric ID
            
        Returns:
            Metric or None if not found
        """
        query = select(MetricsCatalog).where(
            and_(
                MetricsCatalog.tenant_id == tenant_id,
                MetricsCatalog.id == metric_id,
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_metric(
        self,
        tenant_id: UUID,
        name: str,
        display_name: str,
        description: str,
        category: str,
        sql_template: str,
        aggregation: str,
        parameters: Optional[Dict[str, Any]] = None,
        unit: Optional[str] = None,
        tags: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
    ) -> MetricsCatalog:
        """Create a new metric.
        
        Args:
            tenant_id: Tenant ID
            name: Metric name (unique per tenant)
            display_name: Human-readable name
            description: Metric description
            category: Metric category
            sql_template: SQL template
            aggregation: Aggregation method
            parameters: Parameter definitions (optional)
            unit: Unit of measurement (optional)
            tags: Tags for filtering (optional)
            embedding: Semantic embedding (optional)
            
        Returns:
            Created metric
            
        Raises:
            ValueError: If metric with same name already exists
        """
        # Check if metric already exists
        existing = await self.get_metric(tenant_id, name)
        if existing:
            raise ValueError(f"Metric with name '{name}' already exists")
        
        # Create metric
        metric = MetricsCatalog(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            sql_template=sql_template,
            aggregation=aggregation,
            parameters=parameters,
            unit=unit,
            tags=tags,
            embedding=embedding,
            is_active=True,
        )
        
        self.session.add(metric)
        await self.session.flush()
        await self.session.refresh(metric)
        
        return metric
    
    async def update_metric(
        self,
        tenant_id: UUID,
        metric_name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        sql_template: Optional[str] = None,
        aggregation: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        unit: Optional[str] = None,
        tags: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
    ) -> Optional[MetricsCatalog]:
        """Update an existing metric.
        
        Args:
            tenant_id: Tenant ID
            metric_name: Metric name
            display_name: New display name (optional)
            description: New description (optional)
            category: New category (optional)
            sql_template: New SQL template (optional)
            aggregation: New aggregation (optional)
            parameters: New parameters (optional)
            unit: New unit (optional)
            tags: New tags (optional)
            embedding: New embedding (optional)
            
        Returns:
            Updated metric or None if not found
        """
        metric = await self.get_metric(tenant_id, metric_name)
        if not metric:
            return None
        
        # Update fields
        if display_name is not None:
            metric.display_name = display_name
        if description is not None:
            metric.description = description
        if category is not None:
            metric.category = category
        if sql_template is not None:
            metric.sql_template = sql_template
        if aggregation is not None:
            metric.aggregation = aggregation
        if parameters is not None:
            metric.parameters = parameters
        if unit is not None:
            metric.unit = unit
        if tags is not None:
            metric.tags = tags
        if embedding is not None:
            metric.embedding = embedding
        
        await self.session.flush()
        await self.session.refresh(metric)
        
        return metric
    
    async def deprecate_metric(
        self,
        tenant_id: UUID,
        metric_name: str,
    ) -> Optional[MetricsCatalog]:
        """Deprecate a metric (mark as inactive).
        
        Args:
            tenant_id: Tenant ID
            metric_name: Metric name
            
        Returns:
            Deprecated metric or None if not found
        """
        metric = await self.get_metric(tenant_id, metric_name)
        if not metric:
            return None
        
        metric.is_active = False
        
        await self.session.flush()
        await self.session.refresh(metric)
        
        return metric
    
    async def activate_metric(
        self,
        tenant_id: UUID,
        metric_name: str,
    ) -> Optional[MetricsCatalog]:
        """Activate a deprecated metric.
        
        Args:
            tenant_id: Tenant ID
            metric_name: Metric name
            
        Returns:
            Activated metric or None if not found
        """
        metric = await self.get_metric(tenant_id, metric_name)
        if not metric:
            return None
        
        metric.is_active = True
        
        await self.session.flush()
        await self.session.refresh(metric)
        
        return metric
    
    async def search_metrics(
        self,
        tenant_id: UUID,
        query: str,
        limit: int = 10,
    ) -> List[MetricsCatalog]:
        """Search metrics by name, display name, or description.
        
        Args:
            tenant_id: Tenant ID
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching metrics
        """
        search_pattern = f"%{query}%"
        
        stmt = select(MetricsCatalog).where(
            and_(
                MetricsCatalog.tenant_id == tenant_id,
                MetricsCatalog.is_active == True,
                (
                    MetricsCatalog.name.ilike(search_pattern) |
                    MetricsCatalog.display_name.ilike(search_pattern) |
                    MetricsCatalog.description.ilike(search_pattern)
                )
            )
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

