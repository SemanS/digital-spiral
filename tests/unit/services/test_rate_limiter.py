"""Unit tests for RateLimiter."""

import pytest
import asyncio
from uuid import uuid4

from src.application.services.rate_limiter import (
    InMemoryRateLimiter,
    RateLimitError,
)


@pytest.fixture
def instance_id():
    """Create a test instance ID."""
    return uuid4()


@pytest.fixture
def rate_limiter():
    """Create an in-memory rate limiter."""
    return InMemoryRateLimiter(default_limit=5, default_window=1)


class TestInMemoryRateLimiter:
    """Tests for InMemoryRateLimiter."""

    async def test_allows_requests_under_limit(self, rate_limiter, instance_id):
        """Test that requests under the limit are allowed."""
        # Should allow 5 requests
        for i in range(5):
            result = await rate_limiter.check(instance_id)
            assert result is True

    async def test_blocks_requests_over_limit(self, rate_limiter, instance_id):
        """Test that requests over the limit are blocked."""
        # Use up the limit
        for i in range(5):
            await rate_limiter.check(instance_id)

        # Next request should be blocked
        with pytest.raises(RateLimitError) as exc_info:
            await rate_limiter.check(instance_id)

        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.retry_after > 0

    async def test_custom_limit(self, instance_id):
        """Test rate limiter with custom limit."""
        limiter = InMemoryRateLimiter(default_limit=3, default_window=1)

        # Should allow 3 requests
        for i in range(3):
            await limiter.check(instance_id)

        # 4th request should be blocked
        with pytest.raises(RateLimitError):
            await limiter.check(instance_id)

    async def test_custom_window(self, instance_id):
        """Test rate limiter with custom window."""
        limiter = InMemoryRateLimiter(default_limit=5, default_window=2)

        # Use up the limit
        for i in range(5):
            await limiter.check(instance_id)

        # Should be blocked
        with pytest.raises(RateLimitError) as exc_info:
            await limiter.check(instance_id)

        # Retry after should be close to window size
        assert exc_info.value.retry_after <= 2

    async def test_different_instances_independent(self, rate_limiter):
        """Test that different instances have independent limits."""
        instance1 = uuid4()
        instance2 = uuid4()

        # Use up limit for instance1
        for i in range(5):
            await rate_limiter.check(instance1)

        # instance1 should be blocked
        with pytest.raises(RateLimitError):
            await rate_limiter.check(instance1)

        # instance2 should still work
        result = await rate_limiter.check(instance2)
        assert result is True

    async def test_get_remaining(self, rate_limiter, instance_id):
        """Test getting remaining requests."""
        # Initially should have full limit
        remaining = await rate_limiter.get_remaining(instance_id)
        assert remaining == 5

        # After 2 requests
        await rate_limiter.check(instance_id)
        await rate_limiter.check(instance_id)

        remaining = await rate_limiter.get_remaining(instance_id)
        assert remaining == 3

        # After using all
        for i in range(3):
            await rate_limiter.check(instance_id)

        remaining = await rate_limiter.get_remaining(instance_id)
        assert remaining == 0

    async def test_reset(self, rate_limiter, instance_id):
        """Test resetting rate limit."""
        # Use up the limit
        for i in range(5):
            await rate_limiter.check(instance_id)

        # Should be blocked
        with pytest.raises(RateLimitError):
            await rate_limiter.check(instance_id)

        # Reset
        await rate_limiter.reset(instance_id)

        # Should work again
        result = await rate_limiter.check(instance_id)
        assert result is True

        remaining = await rate_limiter.get_remaining(instance_id)
        assert remaining == 4

    async def test_window_expiration(self, instance_id):
        """Test that window expires and resets."""
        limiter = InMemoryRateLimiter(default_limit=2, default_window=1)

        # Use up the limit
        await limiter.check(instance_id)
        await limiter.check(instance_id)

        # Should be blocked
        with pytest.raises(RateLimitError):
            await limiter.check(instance_id)

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Should work again
        result = await limiter.check(instance_id)
        assert result is True

    async def test_per_instance_limit_override(self, rate_limiter, instance_id):
        """Test overriding limit per request."""
        # Use custom limit of 3 instead of default 5
        for i in range(3):
            await rate_limiter.check(instance_id, limit=3)

        # Should be blocked with limit=3
        with pytest.raises(RateLimitError):
            await rate_limiter.check(instance_id, limit=3)

        # But should still work with default limit=5
        result = await rate_limiter.check(instance_id)
        assert result is True

    async def test_retry_after_decreases(self, instance_id):
        """Test that retry_after decreases over time."""
        limiter = InMemoryRateLimiter(default_limit=1, default_window=2)

        # Use up the limit
        await limiter.check(instance_id)

        # Get first retry_after
        try:
            await limiter.check(instance_id)
        except RateLimitError as e:
            retry_after_1 = e.retry_after

        # Wait a bit
        await asyncio.sleep(0.5)

        # Get second retry_after
        try:
            await limiter.check(instance_id)
        except RateLimitError as e:
            retry_after_2 = e.retry_after

        # Should be less
        assert retry_after_2 < retry_after_1

    async def test_concurrent_requests(self, rate_limiter, instance_id):
        """Test handling concurrent requests."""
        # Make 10 concurrent requests (limit is 5)
        tasks = [rate_limiter.check(instance_id) for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should have 5 successes and 5 failures
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if isinstance(r, RateLimitError))

        assert successes == 5
        assert failures == 5

