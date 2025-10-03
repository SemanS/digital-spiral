"""Cached repository wrapper."""

from __future__ import annotations

import json
from typing import Generic, TypeVar
from uuid import UUID

from src.application.interfaces import IRepository
from src.infrastructure.cache import CacheService

ModelType = TypeVar("ModelType")


class CachedRepository(IRepository[ModelType], Generic[ModelType]):
    """
    Repository wrapper that adds caching layer.
    
    This class wraps any repository implementation and adds Redis caching
    for frequently accessed data.
    """

    def __init__(
        self,
        repository: IRepository[ModelType],
        cache: CacheService,
        cache_prefix: str,
        default_ttl: int = 300,  # 5 minutes
    ):
        """
        Initialize cached repository.

        Args:
            repository: Underlying repository implementation
            cache: Cache service instance
            cache_prefix: Prefix for cache keys (e.g., "issue", "project")
            default_ttl: Default TTL in seconds
        """
        self.repository = repository
        self.cache = cache
        self.cache_prefix = cache_prefix
        self.default_ttl = default_ttl

    def _make_key(self, suffix: str) -> str:
        """
        Create cache key.

        Args:
            suffix: Key suffix

        Returns:
            Full cache key
        """
        return f"{self.cache_prefix}:{suffix}"

    def _serialize(self, entity: ModelType) -> str:
        """
        Serialize entity to JSON string.

        Args:
            entity: Entity to serialize

        Returns:
            JSON string
        """
        # Convert entity to dict (assuming entity has __dict__)
        if hasattr(entity, "__dict__"):
            data = {}
            for key, value in entity.__dict__.items():
                if key.startswith("_"):
                    continue
                # Convert UUID to string
                if isinstance(value, UUID):
                    data[key] = str(value)
                else:
                    data[key] = value
            return json.dumps(data, default=str)
        return json.dumps(entity, default=str)

    def _deserialize(self, data: str, entity_class: type) -> ModelType:
        """
        Deserialize JSON string to entity.

        Args:
            data: JSON string
            entity_class: Entity class

        Returns:
            Entity instance
        """
        obj_dict = json.loads(data)
        # Convert string UUIDs back to UUID objects
        for key, value in obj_dict.items():
            if key.endswith("_id") and isinstance(value, str):
                try:
                    obj_dict[key] = UUID(value)
                except (ValueError, AttributeError):
                    pass
        return entity_class(**obj_dict)

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """
        Get entity by ID with caching.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        # Try cache first
        cache_key = self._make_key(f"id:{id}")
        cached = await self.cache.get(cache_key)
        
        if cached is not None:
            # Cache hit
            return self._deserialize(cached, type(self.repository.model_class))
        
        # Cache miss - fetch from repository
        entity = await self.repository.get_by_id(id)
        
        if entity is not None:
            # Store in cache
            await self.cache.set(
                cache_key,
                self._serialize(entity),
                ttl=self.default_ttl
            )
        
        return entity

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get all entities with caching.

        Note: This caches the entire result set, which may not be ideal
        for large datasets. Consider using pagination-specific caching.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        # Cache key includes pagination params
        cache_key = self._make_key(f"all:skip={skip}:limit={limit}")
        cached = await self.cache.get(cache_key)
        
        if cached is not None:
            # Cache hit
            data = json.loads(cached)
            return [
                self._deserialize(item, type(self.repository.model_class))
                for item in data
            ]
        
        # Cache miss - fetch from repository
        entities = await self.repository.get_all(skip=skip, limit=limit)
        
        if entities:
            # Store in cache
            serialized = [self._serialize(e) for e in entities]
            await self.cache.set(
                cache_key,
                json.dumps(serialized),
                ttl=self.default_ttl
            )
        
        return entities

    async def create(self, entity: ModelType) -> ModelType:
        """
        Create new entity and invalidate cache.

        Args:
            entity: Entity to create

        Returns:
            Created entity
        """
        # Create in repository
        created = await self.repository.create(entity)
        
        # Invalidate list caches
        await self._invalidate_list_caches()
        
        # Cache the created entity
        if hasattr(created, "id"):
            cache_key = self._make_key(f"id:{created.id}")
            await self.cache.set(
                cache_key,
                self._serialize(created),
                ttl=self.default_ttl
            )
        
        return created

    async def update(self, entity: ModelType) -> ModelType:
        """
        Update existing entity and invalidate cache.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        # Update in repository
        updated = await self.repository.update(entity)
        
        # Invalidate caches
        if hasattr(updated, "id"):
            cache_key = self._make_key(f"id:{updated.id}")
            await self.cache.delete(cache_key)
        
        await self._invalidate_list_caches()
        
        return updated

    async def delete(self, id: UUID) -> bool:
        """
        Delete entity and invalidate cache.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        # Delete from repository
        deleted = await self.repository.delete(id)
        
        if deleted:
            # Invalidate caches
            cache_key = self._make_key(f"id:{id}")
            await self.cache.delete(cache_key)
            await self._invalidate_list_caches()
        
        return deleted

    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists (uses cache).

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        # Try to get from cache first
        entity = await self.get_by_id(id)
        if entity is not None:
            return True
        
        # Fall back to repository
        return await self.repository.exists(id)

    async def count(self) -> int:
        """
        Count total number of entities with caching.

        Returns:
            Total count
        """
        cache_key = self._make_key("count")
        cached = await self.cache.get(cache_key)
        
        if cached is not None:
            return int(cached)
        
        # Cache miss - fetch from repository
        count = await self.repository.count()
        
        # Store in cache
        await self.cache.set(
            cache_key,
            str(count),
            ttl=self.default_ttl
        )
        
        return count

    async def _invalidate_list_caches(self):
        """Invalidate all list and count caches."""
        # Clear all keys with this prefix
        # Note: This is a simple implementation. For production,
        # consider using cache tags or more sophisticated invalidation
        await self.cache.clear_namespace(self.cache_prefix)


__all__ = ["CachedRepository"]

