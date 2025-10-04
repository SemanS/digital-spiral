"""Analytics API endpoints."""

from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_async_session
from src.domain.schemas.analytics_spec import AnalyticsSpec
from src.application.services.analytics import (
    AnalyticsService,
    AnalyticsSpecValidator,
)
from src.application.services.llm import NLTranslator
from src.api.dependencies import get_current_user, get_tenant_id

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/query")
async def execute_analytics_query(
    spec: AnalyticsSpec,
    use_cache: bool = Query(True, description="Use cache if available"),
    cache_ttl_hours: int = Query(24, ge=1, le=168, description="Cache TTL in hours"),
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Execute analytics query from AnalyticsSpec.
    
    Args:
        spec: Analytics specification
        use_cache: Whether to use cache
        cache_ttl_hours: Cache TTL in hours
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        Query results with metadata
    """
    # Validate spec
    validator = AnalyticsSpecValidator(session, tenant_id)
    validation = await validator.validate(spec, is_job=False)
    
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid AnalyticsSpec",
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }
        )
    
    # Execute query
    service = AnalyticsService(session, tenant_id)
    
    try:
        result = await service.execute_analytics_spec(
            spec=spec,
            use_cache=use_cache,
            cache_ttl_hours=cache_ttl_hours,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/nl")
async def execute_natural_language_query(
    query: str,
    use_cache: bool = Query(True, description="Use cache if available"),
    cache_ttl_hours: int = Query(24, ge=1, le=168, description="Cache TTL in hours"),
    openai_api_key: str = Depends(lambda: "sk-..."),  # TODO: Get from config
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Execute analytics query from natural language.
    
    Args:
        query: Natural language query
        use_cache: Whether to use cache
        cache_ttl_hours: Cache TTL in hours
        openai_api_key: OpenAI API key
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        Query results with metadata and translated spec
    """
    # Translate NL to AnalyticsSpec
    translator = NLTranslator(api_key=openai_api_key)
    
    try:
        spec = await translator.translate(query)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Failed to translate query",
                "error": str(e),
            }
        )
    
    # Validate spec
    validator = AnalyticsSpecValidator(session, tenant_id)
    validation = await validator.validate(spec, is_job=False)
    
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Translated spec is invalid",
                "spec": spec.model_dump(),
                "errors": validation["errors"],
                "warnings": validation["warnings"],
            }
        )
    
    # Execute query
    service = AnalyticsService(session, tenant_id)
    
    try:
        result = await service.execute_analytics_spec(
            spec=spec,
            use_cache=use_cache,
            cache_ttl_hours=cache_ttl_hours,
        )
        
        # Add translated spec to response
        result["translated_spec"] = spec.model_dump()
        result["original_query"] = query
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/validate")
async def validate_analytics_spec(
    spec: AnalyticsSpec,
    is_job: bool = Query(False, description="Whether this is a background job"),
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Validate AnalyticsSpec without executing.
    
    Args:
        spec: Analytics specification
        is_job: Whether this is a background job
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        Validation results
    """
    validator = AnalyticsSpecValidator(session, tenant_id)
    validation = await validator.validate(spec, is_job=is_job)
    
    return validation


@router.get("/metrics")
async def get_available_metrics(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get available metrics for tenant.
    
    Args:
        category: Filter by category
        tags: Filter by tags (comma-separated)
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        List of available metrics
    """
    service = AnalyticsService(session, tenant_id)
    
    tags_list = tags.split(",") if tags else None
    
    metrics = await service.get_available_metrics(
        category=category,
        tags=tags_list,
    )
    
    return {
        "metrics": metrics,
        "count": len(metrics),
    }


@router.get("/metrics/search")
async def search_metrics(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Search metrics by name or description.
    
    Args:
        q: Search query
        limit: Maximum results
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        List of matching metrics
    """
    service = AnalyticsService(session, tenant_id)
    
    metrics = await service.search_metrics(query=q, limit=limit)
    
    return {
        "metrics": metrics,
        "count": len(metrics),
        "query": q,
    }


@router.post("/cache/invalidate")
async def invalidate_cache(
    spec: Optional[AnalyticsSpec] = None,
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Invalidate analytics cache.
    
    Args:
        spec: Specific spec to invalidate (optional, if None invalidates all)
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        Invalidation results
    """
    service = AnalyticsService(session, tenant_id)
    
    result = await service.invalidate_cache(spec)
    
    return result


@router.get("/cache/stats")
async def get_cache_stats(
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Get cache statistics.
    
    Args:
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        Cache statistics
    """
    service = AnalyticsService(session, tenant_id)
    
    stats = await service.get_cache_stats()
    
    return stats


@router.post("/cache/cleanup")
async def cleanup_expired_cache(
    session: AsyncSession = Depends(get_async_session),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """Clean up expired cache entries.
    
    Args:
        session: Database session
        tenant_id: Tenant ID
        
    Returns:
        Cleanup results
    """
    service = AnalyticsService(session, tenant_id)
    
    result = await service.cleanup_expired_cache()
    
    return result

