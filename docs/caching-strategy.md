# Caching Strategy

This document describes the caching strategy used in Digital Spiral for optimizing database access and improving performance.

## Overview

Digital Spiral uses a multi-layer caching strategy:

1. **Redis Cache** - For frequently accessed data (issues, projects, users)
2. **Materialized Views** - For complex aggregations and analytics
3. **Application Cache** - For session data and temporary state

## Redis Caching

### Cache Service

The `CacheService` class provides a high-level interface for Redis operations:

```python
from src.infrastructure.cache import CacheService

cache = CacheService(namespace="digital_spiral")

# Set value
await cache.set("key", "value", ttl=300)

# Get value
value = await cache.get("key")

# Set JSON
await cache.set_json("user:123", {"name": "John", "email": "john@example.com"})

# Get JSON
user = await cache.get_json("user:123")
```

### Cached Repositories

Cached repositories wrap regular repositories and add caching:

```python
from src.infrastructure.database.repositories import (
    IssueRepository,
    CachedIssueRepository
)
from src.infrastructure.cache import CacheService

# Create regular repository
issue_repo = IssueRepository(session)

# Wrap with caching
cache = CacheService(namespace="issues")
cached_repo = CachedIssueRepository(issue_repo, cache, default_ttl=300)

# Use cached repository
issue = await cached_repo.get_by_key("PROJ-123")  # Cached!
```

## Cache Keys

### Key Naming Convention

Cache keys follow a hierarchical naming convention:

```
{namespace}:{entity_type}:{identifier}:{params}
```

**Examples:**
- `digital_spiral:issue:id:550e8400-e29b-41d4-a716-446655440000`
- `digital_spiral:issue:key:PROJ-123`
- `digital_spiral:issue:project:550e8400:PROJ:skip=0:limit=100`
- `digital_spiral:project:instance:550e8400:skip=0:limit=100`

### Key Patterns

| Pattern | Example | Description |
|---------|---------|-------------|
| `{prefix}:id:{uuid}` | `issue:id:550e8400...` | Single entity by ID |
| `{prefix}:key:{key}` | `issue:key:PROJ-123` | Single entity by key |
| `{prefix}:list:{params}` | `issue:list:skip=0:limit=100` | List of entities |
| `{prefix}:count` | `issue:count` | Total count |
| `{prefix}:search:{query}` | `issue:search:bug` | Search results |

## TTL (Time To Live)

Different data types have different TTL values based on update frequency:

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Single entity (by ID) | 5 minutes | Moderate update frequency |
| Single entity (by key) | 5 minutes | Moderate update frequency |
| List queries | 2 minutes | Changes frequently |
| Search results | 1 minute | Very dynamic |
| Count queries | 5 minutes | Moderate update frequency |
| Analytics data | 15 minutes | Computed from materialized views |

## Cache Invalidation

### Strategies

1. **Time-based (TTL)** - Automatic expiration after TTL
2. **Event-based** - Invalidate on create/update/delete
3. **Manual** - Explicit invalidation via API

### Invalidation Patterns

#### Single Entity Update

```python
async def update_issue(issue: Issue):
    # Update in database
    updated = await repository.update(issue)
    
    # Invalidate specific caches
    await cache.delete(f"issue:id:{issue.id}")
    await cache.delete(f"issue:key:{issue.issue_key}")
    
    # Invalidate list caches
    await cache.clear_namespace("issue")
    
    return updated
```

#### Bulk Operations

```python
async def bulk_update_issues(issues: list[Issue]):
    # Update in database
    updated = await repository.bulk_update(issues)
    
    # Invalidate all issue caches
    await cache.clear_namespace("issue")
    
    return updated
```

#### Cascade Invalidation

When updating a project, invalidate related issues:

```python
async def update_project(project: Project):
    # Update in database
    updated = await repository.update(project)
    
    # Invalidate project cache
    await cache.delete(f"project:id:{project.id}")
    
    # Invalidate related issue caches
    await cache.clear_namespace("issue")
    
    return updated
```

## Cache Warming

Pre-populate cache with frequently accessed data:

```python
async def warm_cache(tenant_id: UUID):
    """Warm cache with frequently accessed data."""
    
    # Get active projects
    projects = await project_repo.get_active(tenant_id)
    
    for project in projects:
        # Cache project
        cache_key = f"project:id:{project.id}"
        await cache.set_json(cache_key, project.__dict__, ttl=300)
        
        # Cache recent issues
        issues = await issue_repo.get_by_project(
            tenant_id, 
            project.project_key,
            limit=50
        )
        
        for issue in issues:
            cache_key = f"issue:id:{issue.id}"
            await cache.set_json(cache_key, issue.__dict__, ttl=300)
```

## Cache Monitoring

### Cache Hit Rate

Monitor cache effectiveness:

```python
from prometheus_client import Counter, Histogram

cache_hits = Counter('cache_hits_total', 'Total cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Total cache misses', ['cache_type'])

async def get_with_metrics(key: str, cache_type: str):
    value = await cache.get(key)
    
    if value is not None:
        cache_hits.labels(cache_type=cache_type).inc()
    else:
        cache_misses.labels(cache_type=cache_type).inc()
    
    return value
```

### Cache Size

Monitor cache memory usage:

```python
import redis

async def get_cache_stats():
    """Get cache statistics."""
    info = await cache.redis.info('memory')
    
    return {
        'used_memory': info['used_memory_human'],
        'used_memory_peak': info['used_memory_peak_human'],
        'total_keys': await cache.redis.dbsize(),
    }
```

## Best Practices

### 1. Cache What's Expensive

✅ **DO cache:**
- Database queries
- External API calls
- Complex computations
- Frequently accessed data

❌ **DON'T cache:**
- Rapidly changing data
- User-specific sensitive data (without encryption)
- Very large objects (>1MB)

### 2. Use Appropriate TTL

```python
# Short TTL for dynamic data
await cache.set("search:results", data, ttl=60)  # 1 minute

# Medium TTL for moderate data
await cache.set("issue:PROJ-123", data, ttl=300)  # 5 minutes

# Long TTL for static data
await cache.set("config:settings", data, ttl=3600)  # 1 hour
```

### 3. Handle Cache Failures Gracefully

```python
async def get_issue(issue_id: UUID) -> Issue:
    try:
        # Try cache first
        cached = await cache.get_json(f"issue:id:{issue_id}")
        if cached:
            return Issue(**cached)
    except Exception as e:
        logger.warning(f"Cache error: {e}")
        # Continue to database
    
    # Fallback to database
    return await repository.get_by_id(issue_id)
```

### 4. Use Cache Namespaces

```python
# Separate namespaces for different tenants
tenant_cache = CacheService(namespace=f"tenant:{tenant_id}")

# Separate namespaces for different data types
issue_cache = CacheService(namespace="issues")
project_cache = CacheService(namespace="projects")
```

### 5. Implement Cache Versioning

```python
CACHE_VERSION = "v1"

def make_key(entity_type: str, identifier: str) -> str:
    return f"{CACHE_VERSION}:{entity_type}:{identifier}"

# When schema changes, increment version
# Old cache entries will be ignored
```

## Cache Patterns

### Read-Through Cache

```python
async def get_issue(issue_id: UUID) -> Issue:
    """Get issue with read-through caching."""
    cache_key = f"issue:id:{issue_id}"
    
    # Try cache
    cached = await cache.get_json(cache_key)
    if cached:
        return Issue(**cached)
    
    # Cache miss - read from database
    issue = await repository.get_by_id(issue_id)
    
    if issue:
        # Populate cache
        await cache.set_json(cache_key, issue.__dict__, ttl=300)
    
    return issue
```

### Write-Through Cache

```python
async def update_issue(issue: Issue) -> Issue:
    """Update issue with write-through caching."""
    # Update database
    updated = await repository.update(issue)
    
    # Update cache
    cache_key = f"issue:id:{updated.id}"
    await cache.set_json(cache_key, updated.__dict__, ttl=300)
    
    return updated
```

### Cache-Aside (Lazy Loading)

```python
async def get_project(project_id: UUID) -> Project:
    """Get project with cache-aside pattern."""
    cache_key = f"project:id:{project_id}"
    
    # Try cache
    cached = await cache.get_json(cache_key)
    if cached:
        return Project(**cached)
    
    # Cache miss - application loads from database
    project = await repository.get_by_id(project_id)
    
    if project:
        # Application populates cache
        await cache.set_json(cache_key, project.__dict__, ttl=300)
    
    return project
```

## Testing Cache

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_cached_repository_hit():
    """Test cache hit scenario."""
    # Mock cache with data
    cache = AsyncMock()
    cache.get_json.return_value = {"id": "123", "key": "PROJ-1"}
    
    # Mock repository (should not be called)
    repo = AsyncMock()
    
    # Create cached repository
    cached_repo = CachedIssueRepository(repo, cache)
    
    # Get issue
    issue = await cached_repo.get_by_id("123")
    
    # Verify cache was used
    cache.get_json.assert_called_once()
    repo.get_by_id.assert_not_called()

@pytest.mark.asyncio
async def test_cached_repository_miss():
    """Test cache miss scenario."""
    # Mock cache with no data
    cache = AsyncMock()
    cache.get_json.return_value = None
    
    # Mock repository with data
    repo = AsyncMock()
    repo.get_by_id.return_value = Issue(id="123", key="PROJ-1")
    
    # Create cached repository
    cached_repo = CachedIssueRepository(repo, cache)
    
    # Get issue
    issue = await cached_repo.get_by_id("123")
    
    # Verify both cache and repository were used
    cache.get_json.assert_called_once()
    repo.get_by_id.assert_called_once()
    cache.set_json.assert_called_once()
```

## Troubleshooting

### Issue: Cache not invalidating

**Cause:** Incorrect cache key or namespace

**Solution:**
```python
# Ensure consistent key generation
def make_cache_key(entity_type: str, id: UUID) -> str:
    return f"{entity_type}:id:{id}"

# Use the same function everywhere
cache_key = make_cache_key("issue", issue_id)
```

### Issue: Memory usage too high

**Cause:** Too many cached items or large objects

**Solutions:**
1. Reduce TTL
2. Implement cache size limits
3. Use Redis maxmemory policy

```python
# Configure Redis maxmemory
# redis.conf:
# maxmemory 2gb
# maxmemory-policy allkeys-lru
```

### Issue: Stale data in cache

**Cause:** Insufficient cache invalidation

**Solution:**
```python
# Implement comprehensive invalidation
async def update_issue(issue: Issue):
    updated = await repository.update(issue)
    
    # Invalidate all related caches
    await cache.delete(f"issue:id:{issue.id}")
    await cache.delete(f"issue:key:{issue.issue_key}")
    await cache.clear_namespace(f"issue:project:{issue.project_id}")
    
    return updated
```

