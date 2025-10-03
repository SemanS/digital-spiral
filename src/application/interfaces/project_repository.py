"""Project repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.domain.entities import Project

from .repository import IRepository


class IProjectRepository(IRepository[Project]):
    """
    Project repository interface.

    Defines operations specific to Project entities.
    """

    @abstractmethod
    async def get_by_key(
        self,
        instance_id: UUID,
        project_key: str,
    ) -> Project | None:
        """
        Get project by key (e.g., "PROJ").

        Args:
            instance_id: Jira instance ID
            project_key: Project key

        Returns:
            Project or None if not found
        """
        pass

    @abstractmethod
    async def get_by_instance(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """
        Get all projects for a Jira instance.

        Args:
            instance_id: Jira instance ID
            skip: Number of projects to skip
            limit: Maximum number of projects to return

        Returns:
            List of projects
        """
        pass

    @abstractmethod
    async def get_active(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """
        Get all active (non-archived) projects.

        Args:
            instance_id: Jira instance ID
            skip: Number of projects to skip
            limit: Maximum number of projects to return

        Returns:
            List of active projects
        """
        pass


__all__ = ["IProjectRepository"]

