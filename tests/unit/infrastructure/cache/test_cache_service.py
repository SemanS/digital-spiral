"""Unit tests for cache service."""

from __future__ import annotations

import pytest
from fakeredis import FakeRedis

from src.infrastructure.cache import CacheService


@pytest.fixture
def redis_client():
    """Create fake Redis client for testing."""
    return FakeRedis(decode_responses=True)


@pytest.fixture
def cache_service(redis_client):
    """Create cache service with fake Redis client."""
    return CacheService(client=redis_client, namespace="test", default_ttl=60)


class TestCacheService:
    """Tests for CacheService."""

    def test_set_and_get(self, cache_service: CacheService):
        """Test setting and getting a value."""
        cache_service.set("key1", "value1")
        assert cache_service.get("key1") == "value1"

    def test_set_and_get_json(self, cache_service: CacheService):
        """Test setting and getting JSON data."""
        data = {"name": "John", "age": 30}
        cache_service.set("user", data)
        assert cache_service.get("user") == data

    def test_get_nonexistent_key(self, cache_service: CacheService):
        """Test getting a non-existent key."""
        assert cache_service.get("nonexistent") is None

    def test_delete(self, cache_service: CacheService):
        """Test deleting a key."""
        cache_service.set("key1", "value1")
        assert cache_service.exists("key1") is True

        cache_service.delete("key1")
        assert cache_service.exists("key1") is False

    def test_exists(self, cache_service: CacheService):
        """Test checking if key exists."""
        assert cache_service.exists("key1") is False

        cache_service.set("key1", "value1")
        assert cache_service.exists("key1") is True

    def test_get_ttl(self, cache_service: CacheService):
        """Test getting TTL for a key."""
        cache_service.set("key1", "value1", ttl=100)
        ttl = cache_service.get_ttl("key1")
        assert 90 <= ttl <= 100  # Allow some variance

    def test_expire(self, cache_service: CacheService):
        """Test setting TTL for an existing key."""
        cache_service.set("key1", "value1", ttl=100)
        cache_service.expire("key1", 200)

        ttl = cache_service.get_ttl("key1")
        assert 190 <= ttl <= 200

    def test_get_many(self, cache_service: CacheService):
        """Test getting multiple values."""
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        cache_service.set("key3", "value3")

        result = cache_service.get_many(["key1", "key2", "key3", "nonexistent"])
        assert result == {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

    def test_set_many(self, cache_service: CacheService):
        """Test setting multiple values."""
        mapping = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        }

        cache_service.set_many(mapping)

        assert cache_service.get("key1") == "value1"
        assert cache_service.get("key2") == "value2"
        assert cache_service.get("key3") == "value3"

    def test_delete_many(self, cache_service: CacheService):
        """Test deleting multiple values."""
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        cache_service.set("key3", "value3")

        deleted = cache_service.delete_many(["key1", "key2"])
        assert deleted == 2

        assert cache_service.exists("key1") is False
        assert cache_service.exists("key2") is False
        assert cache_service.exists("key3") is True

    def test_clear_namespace(self, cache_service: CacheService):
        """Test clearing all keys in namespace."""
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        cache_service.set("key3", "value3")

        deleted = cache_service.clear_namespace()
        assert deleted == 3

        assert cache_service.exists("key1") is False
        assert cache_service.exists("key2") is False
        assert cache_service.exists("key3") is False

    def test_increment(self, cache_service: CacheService):
        """Test incrementing a counter."""
        value = cache_service.increment("counter")
        assert value == 1

        value = cache_service.increment("counter", 5)
        assert value == 6

    def test_decrement(self, cache_service: CacheService):
        """Test decrementing a counter."""
        cache_service.set("counter", "10")

        value = cache_service.decrement("counter")
        assert value == 9

        value = cache_service.decrement("counter", 3)
        assert value == 6

    def test_namespace_isolation(self, redis_client: FakeRedis):
        """Test that different namespaces are isolated."""
        cache1 = CacheService(client=redis_client, namespace="ns1")
        cache2 = CacheService(client=redis_client, namespace="ns2")

        cache1.set("key", "value1")
        cache2.set("key", "value2")

        assert cache1.get("key") == "value1"
        assert cache2.get("key") == "value2"

    def test_key_namespacing(self, cache_service: CacheService):
        """Test that keys are properly namespaced."""
        cache_service.set("key1", "value1")

        # Check that the actual Redis key includes the namespace
        namespaced_key = cache_service._make_key("key1")
        assert namespaced_key == "test:key1"

    def test_set_with_custom_ttl(self, cache_service: CacheService):
        """Test setting value with custom TTL."""
        cache_service.set("key1", "value1", ttl=120)

        ttl = cache_service.get_ttl("key1")
        assert 110 <= ttl <= 120

    def test_empty_get_many(self, cache_service: CacheService):
        """Test get_many with empty list."""
        result = cache_service.get_many([])
        assert result == {}

    def test_empty_set_many(self, cache_service: CacheService):
        """Test set_many with empty dict."""
        result = cache_service.set_many({})
        assert result is True

    def test_empty_delete_many(self, cache_service: CacheService):
        """Test delete_many with empty list."""
        deleted = cache_service.delete_many([])
        assert deleted == 0

    def test_complex_json_data(self, cache_service: CacheService):
        """Test caching complex JSON data."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "tags": ["admin", "user"]},
                {"id": 2, "name": "Bob", "tags": ["user"]},
            ],
            "metadata": {
                "total": 2,
                "page": 1,
            },
        }

        cache_service.set("complex", data)
        retrieved = cache_service.get("complex")

        assert retrieved == data
        assert retrieved["users"][0]["name"] == "Alice"
        assert retrieved["metadata"]["total"] == 2

