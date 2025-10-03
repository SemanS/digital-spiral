"""Base repository interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

# Type variable for entity type
T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """
    Base repository interface for CRUD operations.

    This interface defines the contract that all repositories must implement.
    It follows the Repository pattern to abstract data access logic.
    """

    @abstractmethod
    async def get_by_id(self, id: UUID) -> T | None:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """
        Create new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """
        Update existing entity.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count
        """
        pass


__all__ = ["IRepository"]

