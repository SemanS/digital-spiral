"""Base repository implementation."""

from __future__ import annotations

from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.application.interfaces import IRepository

# Type variable for SQLAlchemy model
ModelType = TypeVar("ModelType")


class BaseRepository(IRepository[ModelType], Generic[ModelType]):
    """
    Base repository implementation with common CRUD operations.

    This class provides concrete implementations of the IRepository interface
    using SQLAlchemy for database operations.
    """

    def __init__(self, session: Session, model_class: Type[ModelType]):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
            model_class: SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        return self.session.get(self.model_class, id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: ModelType) -> ModelType:
        """
        Create new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity
        """
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """
        Update existing entity.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity

    async def delete(self, id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        entity = await self.get_by_id(id)
        if entity is None:
            return False

        self.session.delete(entity)
        self.session.flush()
        return True

    async def exists(self, id: UUID) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        """
        Count total number of entities.

        Returns:
            Total count
        """
        stmt = select(func.count()).select_from(self.model_class)
        result = self.session.execute(stmt)
        return result.scalar_one()


__all__ = ["BaseRepository"]

