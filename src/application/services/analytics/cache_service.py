"""Cache Service for analytics query results."""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import AnalyticsCache
from src.domain.schemas.analytics_spec import AnalyticsSpec


class CacheService:
    """Service for caching analytics query results."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        """Initialize cache service.
        
        Args:
            session: Database session
            tenant_id: Tenant ID
        """
        self.session = session
        self.tenant_id = tenant_id
    
    async def get_cached_result(
        self,
        spec: AnalyticsSpec,
    ) -> Optional[Dict[str, Any]]:
        """Get cached result for analytics spec.
        
        Args:
            spec: Analytics specification
            
        Returns:
            Cached result or None if not found/expired
        """
        # Compute spec hash
        spec_dict = spec.to_cache_key()
        spec_hash = AnalyticsCache.compute_spec_hash(spec_dict)
        
        # Query cache
        query = select(AnalyticsCache).where(
            and_(
                AnalyticsCache.tenant_id == self.tenant_id,
                AnalyticsCache.spec_hash == spec_hash,
            )
        )
        
        result = await self.session.execute(query)
        cache_entry = result.scalar_one_or_none()
        
        # Check if exists and not expired
        if cache_entry and not cache_entry.is_expired:
            return {
                "data": cache_entry.result_data,
                "metadata": {
                    "cached": True,
                    "cached_at": cache_entry.created_at.isoformat(),
                    "expires_at": cache_entry.expires_at.isoformat(),
                    "ttl_seconds": cache_entry.time_to_live_seconds,
                    "row_count": cache_entry.row_count,
                    "execution_time_ms": cache_entry.execution_time_ms,
                }
            }
        
        return None
    
    async def cache_result(
        self,
        spec: AnalyticsSpec,
        sql_query: str,
        result_data: Dict[str, Any],
        row_count: int,
        execution_time_ms: int,
        ttl_hours: int = 24,
    ) -> AnalyticsCache:
        """Cache analytics query result.
        
        Args:
            spec: Analytics specification
            sql_query: SQL query that was executed
            result_data: Query results
            row_count: Number of rows
            execution_time_ms: Execution time in milliseconds
            ttl_hours: Time to live in hours (default: 24)
            
        Returns:
            Created cache entry
        """
        # Compute spec hash
        spec_dict = spec.to_cache_key()
        spec_hash = AnalyticsCache.compute_spec_hash(spec_dict)
        
        # Check if cache entry already exists
        existing = await self._get_cache_entry(spec_hash)
        
        if existing:
            # Update existing entry
            existing.update_results(
                result_data=result_data,
                row_count=row_count,
                execution_time_ms=execution_time_ms,
                ttl_hours=ttl_hours,
            )
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        
        # Create new cache entry
        cache_entry = AnalyticsCache.create_cache_entry(
            tenant_id=self.tenant_id,
            spec=spec_dict,
            sql_query=sql_query,
            result_data=result_data,
            row_count=row_count,
            execution_time_ms=execution_time_ms,
            ttl_hours=ttl_hours,
        )
        
        self.session.add(cache_entry)
        await self.session.flush()
        await self.session.refresh(cache_entry)
        
        return cache_entry
    
    async def invalidate_cache(self, spec: AnalyticsSpec) -> bool:
        """Invalidate cached result for analytics spec.
        
        Args:
            spec: Analytics specification
            
        Returns:
            True if cache was invalidated, False if not found
        """
        # Compute spec hash
        spec_dict = spec.to_cache_key()
        spec_hash = AnalyticsCache.compute_spec_hash(spec_dict)
        
        # Delete cache entry
        stmt = delete(AnalyticsCache).where(
            and_(
                AnalyticsCache.tenant_id == self.tenant_id,
                AnalyticsCache.spec_hash == spec_hash,
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        return result.rowcount > 0
    
    async def invalidate_all_cache(self) -> int:
        """Invalidate all cached results for tenant.
        
        Returns:
            Number of cache entries invalidated
        """
        stmt = delete(AnalyticsCache).where(
            AnalyticsCache.tenant_id == self.tenant_id
        )
        
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        return result.rowcount
    
    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries.
        
        Returns:
            Number of expired entries removed
        """
        stmt = delete(AnalyticsCache).where(
            and_(
                AnalyticsCache.tenant_id == self.tenant_id,
                AnalyticsCache.expires_at < datetime.utcnow(),
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        return result.rowcount
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for tenant.
        
        Returns:
            Dictionary with cache statistics
        """
        # Count total cache entries
        total_query = select(AnalyticsCache).where(
            AnalyticsCache.tenant_id == self.tenant_id
        )
        total_result = await self.session.execute(total_query)
        total_entries = len(list(total_result.scalars().all()))
        
        # Count expired entries
        expired_query = select(AnalyticsCache).where(
            and_(
                AnalyticsCache.tenant_id == self.tenant_id,
                AnalyticsCache.expires_at < datetime.utcnow(),
            )
        )
        expired_result = await self.session.execute(expired_query)
        expired_entries = len(list(expired_result.scalars().all()))
        
        # Get all entries for stats
        all_query = select(AnalyticsCache).where(
            AnalyticsCache.tenant_id == self.tenant_id
        )
        all_result = await self.session.execute(all_query)
        all_entries = list(all_result.scalars().all())
        
        # Calculate stats
        if all_entries:
            total_rows = sum(e.row_count for e in all_entries)
            avg_execution_time = sum(e.execution_time_ms for e in all_entries) / len(all_entries)
            avg_age = sum(e.age_seconds for e in all_entries) / len(all_entries)
        else:
            total_rows = 0
            avg_execution_time = 0
            avg_age = 0
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "total_cached_rows": total_rows,
            "avg_execution_time_ms": int(avg_execution_time),
            "avg_age_seconds": int(avg_age),
        }
    
    async def _get_cache_entry(self, spec_hash: str) -> Optional[AnalyticsCache]:
        """Get cache entry by spec hash.
        
        Args:
            spec_hash: Spec hash
            
        Returns:
            Cache entry or None
        """
        query = select(AnalyticsCache).where(
            and_(
                AnalyticsCache.tenant_id == self.tenant_id,
                AnalyticsCache.spec_hash == spec_hash,
            )
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def refresh_cache(
        self,
        spec: AnalyticsSpec,
        sql_query: str,
        result_data: Dict[str, Any],
        row_count: int,
        execution_time_ms: int,
        ttl_hours: int = 24,
    ) -> AnalyticsCache:
        """Refresh cache entry (invalidate and recreate).
        
        Args:
            spec: Analytics specification
            sql_query: SQL query
            result_data: Query results
            row_count: Number of rows
            execution_time_ms: Execution time
            ttl_hours: Time to live in hours
            
        Returns:
            New cache entry
        """
        # Invalidate existing cache
        await self.invalidate_cache(spec)
        
        # Create new cache entry
        return await self.cache_result(
            spec=spec,
            sql_query=sql_query,
            result_data=result_data,
            row_count=row_count,
            execution_time_ms=execution_time_ms,
            ttl_hours=ttl_hours,
        )

