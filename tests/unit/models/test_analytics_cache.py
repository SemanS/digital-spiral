"""Unit tests for AnalyticsCache model."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from src.infrastructure.database.models import AnalyticsCache


class TestAnalyticsCache:
    """Test AnalyticsCache model."""

    def test_analytics_cache_creation(self):
        """Test creating an AnalyticsCache instance."""
        spec = {"metrics": ["velocity"], "filters": {}}
        spec_hash = AnalyticsCache.compute_spec_hash(spec)

        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash=spec_hash,
            spec=spec,
            sql_query="SELECT * FROM sprints",
            result_data={"rows": [], "count": 0},
            row_count=0,
            execution_time_ms=150,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        assert cache.spec_hash == spec_hash
        assert cache.spec == spec
        assert cache.row_count == 0
        assert cache.execution_time_ms == 150

    def test_analytics_cache_repr(self):
        """Test AnalyticsCache __repr__ method."""
        spec = {"metrics": ["velocity"]}
        spec_hash = AnalyticsCache.compute_spec_hash(spec)

        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash=spec_hash,
            spec=spec,
            sql_query="SELECT 1",
            result_data={},
            row_count=10,
            execution_time_ms=100,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        repr_str = repr(cache)
        assert "AnalyticsCache" in repr_str
        assert spec_hash[:8] in repr_str
        assert "10" in repr_str

    def test_is_expired_property_false(self):
        """Test is_expired property when not expired."""
        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash="test_hash",
            spec={},
            sql_query="SELECT 1",
            result_data={},
            row_count=0,
            execution_time_ms=100,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        assert cache.is_expired is False

    def test_is_expired_property_true(self):
        """Test is_expired property when expired."""
        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash="test_hash",
            spec={},
            sql_query="SELECT 1",
            result_data={},
            row_count=0,
            execution_time_ms=100,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        assert cache.is_expired is True

    def test_time_to_live_seconds(self):
        """Test time_to_live_seconds property."""
        expires_at = datetime.utcnow() + timedelta(hours=2)

        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash="test_hash",
            spec={},
            sql_query="SELECT 1",
            result_data={},
            row_count=0,
            execution_time_ms=100,
            expires_at=expires_at,
        )

        ttl = cache.time_to_live_seconds
        # Should be approximately 2 hours (7200 seconds)
        assert 7190 <= ttl <= 7210

    def test_time_to_live_seconds_zero_when_expired(self):
        """Test time_to_live_seconds returns 0 when expired."""
        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash="test_hash",
            spec={},
            sql_query="SELECT 1",
            result_data={},
            row_count=0,
            execution_time_ms=100,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )

        assert cache.time_to_live_seconds == 0

    def test_age_seconds(self):
        """Test age_seconds property."""
        created_at = datetime.utcnow() - timedelta(minutes=30)

        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash="test_hash",
            spec={},
            sql_query="SELECT 1",
            result_data={},
            row_count=0,
            execution_time_ms=100,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=created_at,
        )

        age = cache.age_seconds
        # Should be approximately 30 minutes (1800 seconds)
        assert 1790 <= age <= 1810

    def test_compute_spec_hash(self):
        """Test compute_spec_hash static method."""
        spec1 = {"metrics": ["velocity"], "filters": {"project": "TEST"}}
        spec2 = {"filters": {"project": "TEST"}, "metrics": ["velocity"]}  # Different order

        hash1 = AnalyticsCache.compute_spec_hash(spec1)
        hash2 = AnalyticsCache.compute_spec_hash(spec2)

        # Hashes should be the same (keys are sorted)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

    def test_compute_spec_hash_different_specs(self):
        """Test compute_spec_hash produces different hashes for different specs."""
        spec1 = {"metrics": ["velocity"]}
        spec2 = {"metrics": ["cycle_time"]}

        hash1 = AnalyticsCache.compute_spec_hash(spec1)
        hash2 = AnalyticsCache.compute_spec_hash(spec2)

        assert hash1 != hash2

    def test_create_cache_entry(self):
        """Test create_cache_entry class method."""
        tenant_id = uuid4()
        spec = {"metrics": ["velocity"]}
        sql_query = "SELECT AVG(velocity) FROM sprints"
        result_data = {"rows": [{"avg": 25.5}], "count": 1}
        row_count = 1
        execution_time_ms = 250

        cache = AnalyticsCache.create_cache_entry(
            tenant_id=tenant_id,
            spec=spec,
            sql_query=sql_query,
            result_data=result_data,
            row_count=row_count,
            execution_time_ms=execution_time_ms,
            ttl_hours=12,
        )

        assert cache.tenant_id == tenant_id
        assert cache.spec == spec
        assert cache.sql_query == sql_query
        assert cache.result_data == result_data
        assert cache.row_count == row_count
        assert cache.execution_time_ms == execution_time_ms
        assert cache.spec_hash == AnalyticsCache.compute_spec_hash(spec)

        # Check TTL is approximately 12 hours
        ttl = cache.time_to_live_seconds
        assert 43100 <= ttl <= 43300  # ~12 hours

    def test_refresh_ttl(self):
        """Test refresh_ttl method."""
        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash="test_hash",
            spec={},
            sql_query="SELECT 1",
            result_data={},
            row_count=0,
            execution_time_ms=100,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        # Refresh with 48 hours TTL
        cache.refresh_ttl(ttl_hours=48)

        ttl = cache.time_to_live_seconds
        # Should be approximately 48 hours (172800 seconds)
        assert 172700 <= ttl <= 172900

    def test_update_results(self):
        """Test update_results method."""
        cache = AnalyticsCache(
            tenant_id=uuid4(),
            spec_hash="test_hash",
            spec={},
            sql_query="SELECT 1",
            result_data={"rows": [], "count": 0},
            row_count=0,
            execution_time_ms=100,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        new_result_data = {"rows": [{"id": 1}, {"id": 2}], "count": 2}
        new_row_count = 2
        new_execution_time_ms = 200

        cache.update_results(
            result_data=new_result_data,
            row_count=new_row_count,
            execution_time_ms=new_execution_time_ms,
            ttl_hours=36,
        )

        assert cache.result_data == new_result_data
        assert cache.row_count == new_row_count
        assert cache.execution_time_ms == new_execution_time_ms

        # Check TTL was refreshed to 36 hours
        ttl = cache.time_to_live_seconds
        assert 129500 <= ttl <= 129700  # ~36 hours

