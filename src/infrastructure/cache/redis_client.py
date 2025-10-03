"""Redis client configuration and connection management."""

from __future__ import annotations

import os
from typing import Any

import redis
from redis import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError


def get_redis_url() -> str:
    """
    Get Redis URL from environment variable.

    Returns:
        Redis URL string

    Raises:
        ValueError: If REDIS_URL is not set
    """
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        # Fallback to individual components
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        password = os.getenv("REDIS_PASSWORD")
        db = int(os.getenv("REDIS_DB", "0"))

        if password:
            redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            redis_url = f"redis://{host}:{port}/{db}"

    return redis_url


def create_redis_client(
    redis_url: str | None = None,
    max_connections: int = 50,
    socket_timeout: float = 5.0,
    socket_connect_timeout: float = 5.0,
    decode_responses: bool = True,
) -> Redis:
    """
    Create Redis client with connection pooling.

    Args:
        redis_url: Redis URL (defaults to REDIS_URL env var)
        max_connections: Maximum number of connections in the pool
        socket_timeout: Socket timeout in seconds
        socket_connect_timeout: Socket connect timeout in seconds
        decode_responses: Whether to decode responses to strings

    Returns:
        Redis client instance
    """
    if redis_url is None:
        redis_url = get_redis_url()

    # Create connection pool
    pool = ConnectionPool.from_url(
        redis_url,
        max_connections=max_connections,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_connect_timeout,
        decode_responses=decode_responses,
    )

    # Create Redis client
    client = Redis(connection_pool=pool)

    return client


# Global Redis client (initialized on first use)
_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """
    Get or create global Redis client.

    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = create_redis_client()
    return _redis_client


def ping_redis(client: Redis | None = None) -> bool:
    """
    Check if Redis is available.

    Args:
        client: Redis client (uses global client if not provided)

    Returns:
        True if Redis is available, False otherwise
    """
    if client is None:
        client = get_redis_client()

    try:
        return client.ping()
    except (ConnectionError, TimeoutError):
        return False


def close_redis_client(client: Redis | None = None) -> None:
    """
    Close Redis client and connection pool.

    Args:
        client: Redis client (uses global client if not provided)
    """
    global _redis_client

    if client is None:
        client = _redis_client

    if client is not None:
        client.close()

        # Clear global client if it was closed
        if client is _redis_client:
            _redis_client = None


__all__ = [
    "get_redis_url",
    "create_redis_client",
    "get_redis_client",
    "ping_redis",
    "close_redis_client",
]

