"""Rate limiter service using Redis token bucket algorithm."""

from datetime import datetime
from typing import Optional
from uuid import UUID

try:
    import redis.asyncio as redis
except ImportError:
    import redis


class RateLimitError(Exception):
    """Rate limit exceeded exception."""

    def __init__(self, message: str, retry_after: int):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds until retry is allowed
        """
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


class RateLimiter:
    """Token bucket rate limiter using Redis.

    Implements a sliding window rate limiter with Redis.
    Each instance has a configurable rate limit (requests per window).
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        default_limit: int = 100,
        default_window: int = 60,
    ):
        """Initialize the rate limiter.

        Args:
            redis_client: Redis client instance
            default_limit: Default requests per window (default: 100)
            default_window: Default window size in seconds (default: 60)
        """
        self.redis = redis_client
        self.default_limit = default_limit
        self.default_window = default_window

    async def check(
        self,
        instance_id: UUID,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            instance_id: Instance ID to rate limit
            limit: Requests per window (uses default if None)
            window: Window size in seconds (uses default if None)

        Returns:
            True if request is allowed

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        limit = limit or self.default_limit
        window = window or self.default_window

        key = f"rate_limit:{instance_id}"

        # Get current count
        try:
            count = await self.redis.get(key)
        except AttributeError:
            # Fallback for sync redis client
            count = self.redis.get(key)

        if count is None:
            # First request in window
            try:
                await self.redis.setex(key, window, 1)
            except AttributeError:
                self.redis.setex(key, window, 1)
            return True

        count = int(count)
        if count >= limit:
            # Rate limit exceeded
            try:
                ttl = await self.redis.ttl(key)
            except AttributeError:
                ttl = self.redis.ttl(key)

            raise RateLimitError(
                f"Rate limit exceeded for instance {instance_id}. "
                f"Limit: {limit} requests per {window}s",
                retry_after=ttl if ttl > 0 else window,
            )

        # Increment counter
        try:
            await self.redis.incr(key)
        except AttributeError:
            self.redis.incr(key)

        return True

    async def get_remaining(
        self,
        instance_id: UUID,
        limit: Optional[int] = None,
    ) -> int:
        """Get remaining requests for instance.

        Args:
            instance_id: Instance ID
            limit: Requests per window (uses default if None)

        Returns:
            Number of remaining requests
        """
        limit = limit or self.default_limit
        key = f"rate_limit:{instance_id}"

        try:
            count = await self.redis.get(key)
        except AttributeError:
            count = self.redis.get(key)

        if count is None:
            return limit

        count = int(count)
        return max(0, limit - count)

    async def reset(self, instance_id: UUID) -> None:
        """Reset rate limit for instance.

        Args:
            instance_id: Instance ID to reset
        """
        key = f"rate_limit:{instance_id}"
        try:
            await self.redis.delete(key)
        except AttributeError:
            self.redis.delete(key)


class InMemoryRateLimiter:
    """In-memory rate limiter for testing/development.

    Not recommended for production use.
    """

    def __init__(
        self,
        default_limit: int = 100,
        default_window: int = 60,
    ):
        """Initialize the in-memory rate limiter.

        Args:
            default_limit: Default requests per window
            default_window: Default window size in seconds
        """
        self.default_limit = default_limit
        self.default_window = default_window
        self._counters: dict[str, tuple[int, datetime]] = {}

    async def check(
        self,
        instance_id: UUID,
        limit: Optional[int] = None,
        window: Optional[int] = None,
    ) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            instance_id: Instance ID to rate limit
            limit: Requests per window (uses default if None)
            window: Window size in seconds (uses default if None)

        Returns:
            True if request is allowed

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        limit = limit or self.default_limit
        window = window or self.default_window

        key = str(instance_id)
        now = datetime.utcnow()

        if key not in self._counters:
            self._counters[key] = (1, now)
            return True

        count, start_time = self._counters[key]
        elapsed = (now - start_time).total_seconds()

        if elapsed >= window:
            # Window expired, reset
            self._counters[key] = (1, now)
            return True

        if count >= limit:
            # Rate limit exceeded
            retry_after = max(1, int(window - elapsed))  # Ensure at least 1 second
            raise RateLimitError(
                f"Rate limit exceeded for instance {instance_id}. "
                f"Limit: {limit} requests per {window}s",
                retry_after=retry_after,
            )

        # Increment counter
        self._counters[key] = (count + 1, start_time)
        return True

    async def get_remaining(
        self,
        instance_id: UUID,
        limit: Optional[int] = None,
    ) -> int:
        """Get remaining requests for instance.

        Args:
            instance_id: Instance ID
            limit: Requests per window (uses default if None)

        Returns:
            Number of remaining requests
        """
        limit = limit or self.default_limit
        key = str(instance_id)

        if key not in self._counters:
            return limit

        count, _ = self._counters[key]
        return max(0, limit - count)

    async def reset(self, instance_id: UUID) -> None:
        """Reset rate limit for instance.

        Args:
            instance_id: Instance ID to reset
        """
        key = str(instance_id)
        if key in self._counters:
            del self._counters[key]


__all__ = ["RateLimiter", "RateLimitError", "InMemoryRateLimiter"]

