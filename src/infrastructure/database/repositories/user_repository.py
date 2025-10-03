"""User repository implementation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.application.interfaces import IUserRepository
from src.domain.entities import User as UserEntity
from src.infrastructure.database.models import User as UserModel

from .base import BaseRepository


class UserRepository(BaseRepository[UserModel], IUserRepository):
    """
    User repository implementation.

    Provides database operations for User entities.
    """

    def __init__(self, session: Session):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, UserModel)

    async def get_by_account_id(
        self,
        instance_id: UUID,
        account_id: str,
    ) -> UserEntity | None:
        """
        Get user by Jira account ID.

        Args:
            instance_id: Jira instance ID
            account_id: Jira account ID

        Returns:
            User entity or None if not found
        """
        stmt = select(UserModel).where(
            UserModel.instance_id == instance_id,
            UserModel.account_id == account_id,
        )
        result = self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    async def get_by_instance(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserEntity]:
        """
        Get all users for a Jira instance.

        Args:
            instance_id: Jira instance ID
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List of user entities
        """
        stmt = (
            select(UserModel)
            .where(UserModel.instance_id == instance_id)
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_active(
        self,
        instance_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserEntity]:
        """
        Get all active users.

        Args:
            instance_id: Jira instance ID
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            List of active user entities
        """
        stmt = (
            select(UserModel)
            .where(
                UserModel.instance_id == instance_id,
                UserModel.is_active == True,
            )
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def search_by_email(
        self,
        instance_id: UUID,
        email: str,
    ) -> UserEntity | None:
        """
        Search user by email address.

        Args:
            instance_id: Jira instance ID
            email: Email address

        Returns:
            User entity or None if not found
        """
        stmt = select(UserModel).where(
            UserModel.instance_id == instance_id,
            UserModel.email_address == email,
        )
        result = self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._to_entity(model)

    def _to_entity(self, model: UserModel) -> UserEntity:
        """Convert SQLAlchemy model to domain entity."""
        return UserEntity(
            id=model.id,
            instance_id=model.instance_id,
            account_id=model.account_id,
            display_name=model.display_name,
            account_type=model.account_type,
            email_address=model.email_address,
            avatar_url=model.avatar_url,
            is_active=model.is_active,
            created_at=model.jira_created_at,
            updated_at=model.jira_updated_at,
            raw_data=dict(model.raw_jsonb) if model.raw_jsonb else {},
        )

    def _to_model(self, entity: UserEntity) -> UserModel:
        """Convert domain entity to SQLAlchemy model."""
        return UserModel(
            id=entity.id,
            instance_id=entity.instance_id,
            account_id=entity.account_id,
            account_type=entity.account_type,
            display_name=entity.display_name,
            email_address=entity.email_address,
            avatar_url=entity.avatar_url,
            is_active=entity.is_active,
            jira_created_at=entity.created_at,
            jira_updated_at=entity.updated_at,
            raw_jsonb=entity.raw_data,
        )


__all__ = ["UserRepository"]

