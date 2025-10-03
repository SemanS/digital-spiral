"""Project repository implementation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.application.interfaces import IProjectRepository
from src.domain.entities import Project as ProjectEntity
from src.infrastructure.database.models import Project as ProjectModel

from .base import BaseRepository


class ProjectRepository(BaseRepository[ProjectModel], IProjectRepository):
    """
    Project repository implementation.

    Provides database operations for Project entities.
    """

    def __init__(self, session: Session):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, ProjectModel)

    async def get_by_key(
        self,
        instance_id: UUID,
        project_key: str,
    ) -> ProjectEntity | None:
        """
        Get project by key (e.g., "PROJ").

        Args:
            instance_id: Jira instance ID
            project_key: Project key

        Returns:
            Project entity or None if not found
        """
        stmt = select(ProjectModel).where(
            ProjectModel.instance_id == instance_id,
            ProjectModel.project_key == project_key,
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
    ) -> list[ProjectEntity]:
        """
        Get all projects for a Jira instance.

        Args:
            instance_id: Jira instance ID
            skip: Number of projects to skip
            limit: Maximum number of projects to return

        Returns:
            List of project entities
        """
        stmt = (
            select(ProjectModel)
            .where(ProjectModel.instance_id == instance_id)
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
    ) -> list[ProjectEntity]:
        """
        Get all active (non-archived) projects.

        Args:
            instance_id: Jira instance ID
            skip: Number of projects to skip
            limit: Maximum number of projects to return

        Returns:
            List of active project entities
        """
        stmt = (
            select(ProjectModel)
            .where(
                ProjectModel.instance_id == instance_id,
                ProjectModel.is_archived == False,
            )
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: ProjectModel) -> ProjectEntity:
        """Convert SQLAlchemy model to domain entity."""
        return ProjectEntity(
            id=model.id,
            instance_id=model.instance_id,
            project_key=model.project_key,
            project_id=model.project_id,
            name=model.name,
            description=model.description,
            project_type=model.project_type,
            lead_account_id=model.lead_account_id,
            avatar_url=model.avatar_url,
            url=model.url,
            is_archived=model.is_archived,
            is_private=model.is_private,
            created_at=model.jira_created_at,
            updated_at=model.jira_updated_at,
            raw_data=dict(model.raw_jsonb) if model.raw_jsonb else {},
        )

    def _to_model(self, entity: ProjectEntity) -> ProjectModel:
        """Convert domain entity to SQLAlchemy model."""
        return ProjectModel(
            id=entity.id,
            instance_id=entity.instance_id,
            project_key=entity.project_key,
            project_id=entity.project_id,
            name=entity.name,
            description=entity.description,
            project_type=entity.project_type,
            lead_account_id=entity.lead_account_id,
            avatar_url=entity.avatar_url,
            url=entity.url,
            is_archived=entity.is_archived,
            is_private=entity.is_private,
            jira_created_at=entity.created_at,
            jira_updated_at=entity.updated_at,
            raw_jsonb=entity.raw_data,
        )


__all__ = ["ProjectRepository"]

