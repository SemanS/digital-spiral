"""User repository interface."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.domain.entities import User

from .repository import IRepository


class IUserRepository(IRepository[User]):
    """
    User repository interface.

    Defines operations specific to User entities.
    """

    @abstractmethod
    async def get_by_account_id(
        self,
        instance_id: UUID,
        account_id: str,
    ) -> User | None:
        """
        Get user by Jira account ID.

        Args:
            instance_id: Jira instance ID
            account_id: Jira account ID

        Returns:
            User or None if not found
        """
        pass

    @abstractmethod
    async def get_by_instance(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get all users for a Jira instance.

        Args:
            instance_id: Jira instance ID
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List of users
        """
        pass

    @abstractmethod
    async def get_active(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get all active users.

        Args:
            instance_id: Jira instance ID
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List of active users
        """
        pass

    @abstractmethod
    async def search_by_email(
        self,
        instance_id: UUID,
        email: str,
    ) -> User | None:
        """
        Search user by email address.

        Args:
            instance_id: Jira instance ID
            email: Email address

        Returns:
            User or None if not found
        """
        pass


__all__ = ["IUserRepository"]

