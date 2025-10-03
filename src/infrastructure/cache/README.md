# Cache Infrastructure

This directory contains Redis caching infrastructure for Digital Spiral.

## Overview

The cache layer provides:
- **Redis client** with connection pooling
- **Cache service** with TTL support and key namespacing
- **JSON serialization** for complex data structures
- **Batch operations** for efficient multi-key operations
- **Namespace isolation** for multi-tenant support

## Quick Start

### Basic Usage

```python
from src.infrastructure.cache import CacheService

# Create cache service
cache = CacheService(namespace="tenant:123", default_ttl=3600)

# Set and get values
cache.set("issue:PROJ-1", {"summary": "Fix bug", "status": "Done"})
issue = cache.get("issue:PROJ-1")

# Check if key exists
if cache.exists("issue:PROJ-1"):
    print("Issue is cached")

# Delete key
cache.delete("issue:PROJ-1")
```

### Batch Operations

```python
# Set multiple values at once
cache.set_many({
    "issue:PROJ-1": {"summary": "Bug 1"},
    "issue:PROJ-2": {"summary": "Bug 2"},
    "issue:PROJ-3": {"summary": "Bug 3"},
}, ttl=1800)

# Get multiple values
issues = cache.get_many(["issue:PROJ-1", "issue:PROJ-2", "issue:PROJ-3"])

# Delete multiple values
cache.delete_many(["issue:PROJ-1", "issue:PROJ-2"])
```

### Counters

```python
# Increment counter
views = cache.increment("page:views")
views = cache.increment("page:views", amount=5)

# Decrement counter
cache.decrement("inventory:stock", amount=1)
```

### TTL Management

```python
# Set with custom TTL
cache.set("temp:data", "value", ttl=300)  # 5 minutes

# Get remaining TTL
ttl = cache.get_ttl("temp:data")

# Update TTL for existing key
cache.expire("temp:data", 600)  # Extend to 10 minutes
```

## Caching Strategy

### What to Cache

1. **Jira API Responses**
   - Issue details (TTL: 5 minutes)
   - Project metadata (TTL: 1 hour)
   - User information (TTL: 1 hour)
   - Custom field definitions (TTL: 24 hours)

2. **Computed Data**
   - Search results (TTL: 2 minutes)
   - Aggregations (TTL: 5 minutes)
   - AI predictions (TTL: 10 minutes)

3. **Session Data**
   - User sessions (TTL: 30 minutes)
   - Rate limit counters (TTL: 1 minute)
   - Temporary tokens (TTL: 15 minutes)

### Cache Key Naming Convention

Use hierarchical keys with colons as separators:

```
{namespace}:{entity_type}:{entity_id}:{attribute}
```

Examples:
- `tenant:123:issue:PROJ-1` - Issue data
- `tenant:123:project:PROJ` - Project data
- `tenant:123:user:account123` - User data
- `tenant:123:search:jql:hash123` - Search results
- `tenant:123:ratelimit:api:10.0.0.1` - Rate limit counter

### Cache Invalidation

#### Time-based (TTL)
Most cache entries use TTL for automatic expiration.

#### Event-based
Invalidate cache when data changes:

```python
# When issue is updated
cache.delete(f"issue:{issue_key}")

# When project is updated
cache.delete(f"project:{project_key}")

# Clear all issues for a project
cache.clear_namespace()  # Clears all keys in namespace
```

#### Pattern-based
Use Redis SCAN for pattern-based invalidation:

```python
# Clear all issues
pattern = f"{namespace}:issue:*"
keys = redis_client.keys(pattern)
if keys:
    redis_client.delete(*keys)
```

## Multi-Tenant Isolation

Each tenant has its own namespace:

```python
# Tenant 1
cache1 = CacheService(namespace="tenant:123")
cache1.set("issue:PROJ-1", data1)

# Tenant 2
cache2 = CacheService(namespace="tenant:456")
cache2.set("issue:PROJ-1", data2)

# Data is isolated
assert cache1.get("issue:PROJ-1") != cache2.get("issue:PROJ-1")
```

## Performance Considerations

### Connection Pooling

Redis client uses connection pooling (default: 50 connections):

```python
from src.infrastructure.cache import create_redis_client

client = create_redis_client(max_connections=100)
```

### Batch Operations

Use batch operations to reduce round trips:

```python
# Bad: Multiple round trips
for key in keys:
    cache.get(key)

# Good: Single round trip
cache.get_many(keys)
```

### Pipeline for Atomic Operations

```python
# Use pipeline for multiple operations
pipe = cache.client.pipeline()
pipe.set("key1", "value1")
pipe.set("key2", "value2")
pipe.incr("counter")
pipe.execute()
```

## Monitoring

### Health Check

```python
from src.infrastructure.cache import ping_redis

if ping_redis():
    print("Redis is available")
else:
    print("Redis is down")
```

### Metrics

Track cache performance:
- Hit rate (cache hits / total requests)
- Miss rate (cache misses / total requests)
- Eviction rate (keys evicted / total keys)
- Memory usage

## Error Handling

Cache operations should be resilient to Redis failures:

```python
try:
    data = cache.get("key")
    if data is None:
        # Cache miss or Redis down - fetch from source
        data = fetch_from_database()
        cache.set("key", data)
except Exception as e:
    logger.warning(f"Cache error: {e}")
    # Fallback to database
    data = fetch_from_database()
```

## Testing

Use `fakeredis` for unit tests:

```python
import pytest
from fakeredis import FakeRedis
from src.infrastructure.cache import CacheService

@pytest.fixture
def cache_service():
    client = FakeRedis(decode_responses=True)
    return CacheService(client=client, namespace="test")

def test_cache(cache_service):
    cache_service.set("key", "value")
    assert cache_service.get("key") == "value"
```

## Configuration

Environment variables:

```bash
# Redis connection
REDIS_URL=redis://:password@localhost:6379/0

# Or individual components
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=password
REDIS_DB=0
```

## References

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Caching Best Practices](https://redis.io/docs/manual/patterns/)

