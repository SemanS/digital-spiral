"""Cache service for storing and retrieving data from Redis."""

from __future__ import annotations

import json
from typing import Any

from redis import Redis

from .redis_client import get_redis_client


class CacheService:
    """
    Cache service for storing and retrieving data from Redis.

    Provides high-level caching operations with TTL support,
    key namespacing, and JSON serialization.
    """

    def __init__(
        self,
        client: Redis | None = None,
        namespace: str = "ds",
        default_ttl: int = 3600,
    ):
        """
        Initialize cache service.

        Args:
            client: Redis client (uses global client if not provided)
            namespace: Key namespace prefix (e.g., "ds:tenant:123")
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.client = client or get_redis_client()
        self.namespace = namespace
        self.default_ttl = default_ttl

    def _make_key(self, key: str) -> str:
        """
        Create namespaced key.

        Args:
            key: Original key

        Returns:
            Namespaced key (e.g., "ds:tenant:123:issue:PROJ-1")
        """
        return f"{self.namespace}:{key}"

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        namespaced_key = self._make_key(key)
        value = self.client.get(namespaced_key)

        if value is None:
            return None

        # Try to deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # Return as-is if not JSON
            return value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON-serialized if not a string)
            ttl: Time-to-live in seconds (uses default_ttl if not provided)

        Returns:
            True if successful
        """
        namespaced_key = self._make_key(key)
        ttl = ttl or self.default_ttl

        # Serialize value if not a string
        if not isinstance(value, str):
            value = json.dumps(value)

        return self.client.setex(namespaced_key, ttl, value)

    def delete(self, key: str) -> int:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            Number of keys deleted (0 or 1)
        """
        namespaced_key = self._make_key(key)
        return self.client.delete(namespaced_key)

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        namespaced_key = self._make_key(key)
        return self.client.exists(namespaced_key) > 0

    def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds (-1 if no TTL, -2 if key doesn't exist)
        """
        namespaced_key = self._make_key(key)
        return self.client.ttl(namespaced_key)

    def expire(self, key: str, ttl: int) -> bool:
        """
        Set TTL for an existing key.

        Args:
            key: Cache key
            ttl: Time-to-live in seconds

        Returns:
            True if successful
        """
        namespaced_key = self._make_key(key)
        return self.client.expire(namespaced_key, ttl)

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs (only includes existing keys)
        """
        if not keys:
            return {}

        namespaced_keys = [self._make_key(key) for key in keys]
        values = self.client.mget(namespaced_keys)

        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    result[key] = value

        return result

    def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """
        Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time-to-live in seconds (uses default_ttl if not provided)

        Returns:
            True if successful
        """
        if not mapping:
            return True

        ttl = ttl or self.default_ttl

        # Use pipeline for atomic operation
        pipe = self.client.pipeline()

        for key, value in mapping.items():
            namespaced_key = self._make_key(key)

            # Serialize value if not a string
            if not isinstance(value, str):
                value = json.dumps(value)

            pipe.setex(namespaced_key, ttl, value)

        pipe.execute()
        return True

    def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Number of keys deleted
        """
        if not keys:
            return 0

        namespaced_keys = [self._make_key(key) for key in keys]
        return self.client.delete(*namespaced_keys)

    def clear_namespace(self) -> int:
        """
        Clear all keys in the current namespace.

        Returns:
            Number of keys deleted
        """
        pattern = f"{self.namespace}:*"
        keys = self.client.keys(pattern)

        if not keys:
            return 0

        return self.client.delete(*keys)

    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        namespaced_key = self._make_key(key)
        return self.client.incrby(namespaced_key, amount)

    def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrement a counter.

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value after decrement
        """
        namespaced_key = self._make_key(key)
        return self.client.decrby(namespaced_key, amount)


__all__ = ["CacheService"]

