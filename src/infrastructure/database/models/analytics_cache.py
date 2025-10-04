"""Analytics Cache model for query result caching."""

from datetime import datetime, timedelta
from typing import Dict, Any
import hashlib
import json

from sqlalchemy import String, Text, Integer, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin, TenantMixin


class AnalyticsCache(Base, UUIDMixin, TenantMixin):
    """Analytics cache for storing query results.
    
    Caches query results based on AnalyticsSpec hash to avoid
    re-executing expensive queries. Includes TTL for automatic
    expiration.
    """
    
    __tablename__ = "analytics_cache"
    
    # Cache Key
    spec_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="SHA256 hash of AnalyticsSpec (used as cache key)"
    )
    
    # Cached Data
    spec: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Original AnalyticsSpec that generated this cache entry"
    )
    
    sql_query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="SQL query that was executed"
    )
    
    result_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        doc="Query results (rows, metadata, aggregations)"
    )
    
    # Metadata
    row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Number of rows in result set"
    )
    
    execution_time_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Query execution time in milliseconds"
    )
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="When this cache entry expires"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        doc="When this cache entry was created"
    )
    
    # Table arguments
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "spec_hash",
            name="uq_analytics_cache_tenant_hash"
        ),
        Index("idx_analytics_cache_tenant_hash", "tenant_id", "spec_hash"),
        Index("idx_analytics_cache_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of AnalyticsCache."""
        return (
            f"<AnalyticsCache(id={self.id}, spec_hash='{self.spec_hash[:8]}...', "
            f"row_count={self.row_count}, expires_at={self.expires_at})>"
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def time_to_live_seconds(self) -> int:
        """Get remaining TTL in seconds."""
        if self.is_expired:
            return 0
        return int((self.expires_at - datetime.utcnow()).total_seconds())
    
    @property
    def age_seconds(self) -> int:
        """Get cache entry age in seconds."""
        return int((datetime.utcnow() - self.created_at).total_seconds())
    
    @staticmethod
    def compute_spec_hash(spec: Dict[str, Any]) -> str:
        """Compute SHA256 hash of AnalyticsSpec.
        
        Args:
            spec: AnalyticsSpec dictionary
            
        Returns:
            SHA256 hash as hex string
        """
        # Sort keys for consistent hashing
        spec_json = json.dumps(spec, sort_keys=True)
        return hashlib.sha256(spec_json.encode()).hexdigest()
    
    @classmethod
    def create_cache_entry(
        cls,
        tenant_id: str,
        spec: Dict[str, Any],
        sql_query: str,
        result_data: Dict[str, Any],
        row_count: int,
        execution_time_ms: int,
        ttl_hours: int = 24,
    ) -> "AnalyticsCache":
        """Create a new cache entry.
        
        Args:
            tenant_id: Tenant ID
            spec: AnalyticsSpec dictionary
            sql_query: SQL query that was executed
            result_data: Query results
            row_count: Number of rows in result
            execution_time_ms: Query execution time in ms
            ttl_hours: Time to live in hours (default: 24)
            
        Returns:
            New AnalyticsCache instance
        """
        spec_hash = cls.compute_spec_hash(spec)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        return cls(
            tenant_id=tenant_id,
            spec_hash=spec_hash,
            spec=spec,
            sql_query=sql_query,
            result_data=result_data,
            row_count=row_count,
            execution_time_ms=execution_time_ms,
            expires_at=expires_at,
        )
    
    def refresh_ttl(self, ttl_hours: int = 24) -> None:
        """Refresh cache entry TTL.
        
        Args:
            ttl_hours: New time to live in hours
        """
        self.expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
    
    def update_results(
        self,
        result_data: Dict[str, Any],
        row_count: int,
        execution_time_ms: int,
        ttl_hours: int = 24,
    ) -> None:
        """Update cache entry with new results.
        
        Args:
            result_data: New query results
            row_count: New row count
            execution_time_ms: New execution time
            ttl_hours: New time to live in hours
        """
        self.result_data = result_data
        self.row_count = row_count
        self.execution_time_ms = execution_time_ms
        self.refresh_ttl(ttl_hours)

