"""Cached issue repository."""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from src.application.interfaces import IIssueRepository
from src.domain.entities import Issue
from src.infrastructure.cache import CacheService

from .issue_repository import IssueRepository


class CachedIssueRepository(IIssueRepository):
    """
    Cached issue repository.
    
    Adds caching layer on top of IssueRepository for frequently accessed data.
    """

    def __init__(
        self,
        repository: IssueRepository,
        cache: CacheService,
        default_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize cached issue repository.

        Args:
            repository: Underlying issue repository
            cache: Cache service instance
            default_ttl: Default TTL in seconds
        """
        self.repository = repository
        self.cache = cache
        self.cache_prefix = "issue"
        self.default_ttl = default_ttl

    def _make_key(self, suffix: str) -> str:
        """Create cache key."""
        return f"{self.cache_prefix}:{suffix}"

    async def get_by_id(self, id: UUID) -> Issue | None:
        """Get issue by ID with caching."""
        cache_key = self._make_key(f"id:{id}")
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return Issue(**cached)
        
        issue = await self.repository.get_by_id(id)
        
        if issue is not None:
            await self.cache.set_json(cache_key, issue.__dict__, ttl=self.default_ttl)
        
        return issue

    async def get_by_key(self, issue_key: str) -> Issue | None:
        """Get issue by key with caching."""
        cache_key = self._make_key(f"key:{issue_key}")
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return Issue(**cached)
        
        issue = await self.repository.get_by_key(issue_key)
        
        if issue is not None:
            await self.cache.set_json(cache_key, issue.__dict__, ttl=self.default_ttl)
            # Also cache by ID
            id_key = self._make_key(f"id:{issue.id}")
            await self.cache.set_json(id_key, issue.__dict__, ttl=self.default_ttl)
        
        return issue

    async def get_by_instance(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """Get issues by instance with caching."""
        cache_key = self._make_key(f"instance:{instance_id}:skip={skip}:limit={limit}")
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return [Issue(**item) for item in cached]
        
        issues = await self.repository.get_by_instance(instance_id, skip, limit)
        
        if issues:
            await self.cache.set_json(
                cache_key,
                [issue.__dict__ for issue in issues],
                ttl=self.default_ttl
            )
        
        return issues

    async def get_by_project(
        self,
        instance_id: UUID,
        project_key: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """Get issues by project with caching."""
        cache_key = self._make_key(
            f"project:{instance_id}:{project_key}:skip={skip}:limit={limit}"
        )
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return [Issue(**item) for item in cached]
        
        issues = await self.repository.get_by_project(
            instance_id, project_key, skip, limit
        )
        
        if issues:
            await self.cache.set_json(
                cache_key,
                [issue.__dict__ for issue in issues],
                ttl=self.default_ttl
            )
        
        return issues

    async def get_by_assignee(
        self,
        instance_id: UUID,
        assignee_account_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """Get issues by assignee with caching."""
        cache_key = self._make_key(
            f"assignee:{instance_id}:{assignee_account_id}:skip={skip}:limit={limit}"
        )
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return [Issue(**item) for item in cached]
        
        issues = await self.repository.get_by_assignee(
            instance_id, assignee_account_id, skip, limit
        )
        
        if issues:
            await self.cache.set_json(
                cache_key,
                [issue.__dict__ for issue in issues],
                ttl=self.default_ttl
            )
        
        return issues

    async def get_by_status(
        self,
        instance_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """Get issues by status with caching."""
        cache_key = self._make_key(
            f"status:{instance_id}:{status}:skip={skip}:limit={limit}"
        )
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return [Issue(**item) for item in cached]
        
        issues = await self.repository.get_by_status(instance_id, status, skip, limit)
        
        if issues:
            await self.cache.set_json(
                cache_key,
                [issue.__dict__ for issue in issues],
                ttl=self.default_ttl
            )
        
        return issues

    async def get_updated_since(
        self,
        instance_id: UUID,
        since: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """Get issues updated since timestamp (no caching for time-based queries)."""
        # Don't cache time-based queries as they change frequently
        return await self.repository.get_updated_since(instance_id, since, skip, limit)

    async def search(
        self,
        instance_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Issue]:
        """Search issues (with short TTL caching)."""
        cache_key = self._make_key(f"search:{instance_id}:{query}:skip={skip}:limit={limit}")
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return [Issue(**item) for item in cached]
        
        issues = await self.repository.search(instance_id, query, skip, limit)
        
        if issues:
            # Cache search results with shorter TTL (1 minute)
            await self.cache.set_json(
                cache_key,
                [issue.__dict__ for issue in issues],
                ttl=60
            )
        
        return issues

    async def bulk_create(self, issues: list[Issue]) -> list[Issue]:
        """Create multiple issues and invalidate cache."""
        created = await self.repository.bulk_create(issues)
        
        # Invalidate all list caches
        await self.cache.clear_namespace(self.cache_prefix)
        
        return created

    async def bulk_update(self, issues: list[Issue]) -> list[Issue]:
        """Update multiple issues and invalidate cache."""
        updated = await self.repository.bulk_update(issues)
        
        # Invalidate specific issue caches and all list caches
        for issue in updated:
            await self.cache.delete(self._make_key(f"id:{issue.id}"))
            await self.cache.delete(self._make_key(f"key:{issue.issue_key}"))
        
        await self.cache.clear_namespace(self.cache_prefix)
        
        return updated

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Issue]:
        """Get all issues with caching."""
        cache_key = self._make_key(f"all:skip={skip}:limit={limit}")
        cached = await self.cache.get_json(cache_key)
        
        if cached is not None:
            return [Issue(**item) for item in cached]
        
        issues = await self.repository.get_all(skip, limit)
        
        if issues:
            await self.cache.set_json(
                cache_key,
                [issue.__dict__ for issue in issues],
                ttl=self.default_ttl
            )
        
        return issues

    async def create(self, entity: Issue) -> Issue:
        """Create issue and invalidate cache."""
        created = await self.repository.create(entity)
        await self.cache.clear_namespace(self.cache_prefix)
        return created

    async def update(self, entity: Issue) -> Issue:
        """Update issue and invalidate cache."""
        updated = await self.repository.update(entity)
        
        # Invalidate specific caches
        await self.cache.delete(self._make_key(f"id:{updated.id}"))
        await self.cache.delete(self._make_key(f"key:{updated.issue_key}"))
        await self.cache.clear_namespace(self.cache_prefix)
        
        return updated

    async def delete(self, id: UUID) -> bool:
        """Delete issue and invalidate cache."""
        deleted = await self.repository.delete(id)
        
        if deleted:
            await self.cache.delete(self._make_key(f"id:{id}"))
            await self.cache.clear_namespace(self.cache_prefix)
        
        return deleted

    async def exists(self, id: UUID) -> bool:
        """Check if issue exists."""
        return await self.repository.exists(id)

    async def count(self) -> int:
        """Count issues with caching."""
        cache_key = self._make_key("count")
        cached = await self.cache.get(cache_key)
        
        if cached is not None:
            return int(cached)
        
        count = await self.repository.count()
        await self.cache.set(cache_key, str(count), ttl=self.default_ttl)
        
        return count


__all__ = ["CachedIssueRepository"]

