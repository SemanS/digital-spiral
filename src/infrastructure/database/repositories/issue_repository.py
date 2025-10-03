"""Issue repository implementation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.application.interfaces import IIssueRepository
from src.domain.entities import Issue as IssueEntity
from src.infrastructure.database.models import Issue as IssueModel

from .base import BaseRepository


class IssueRepository(BaseRepository[IssueModel], IIssueRepository):
    """
    Issue repository implementation.

    Provides database operations for Issue entities.
    """

    def __init__(self, session: Session):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, IssueModel)

    async def get_by_key(self, issue_key: str) -> IssueEntity | None:
        """
        Get issue by key (e.g., "PROJ-123").

        Args:
            issue_key: Issue key

        Returns:
            Issue entity or None if not found
        """
        stmt = select(IssueModel).where(IssueModel.issue_key == issue_key)
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
    ) -> list[IssueEntity]:
        """
        Get all issues for a Jira instance.

        Args:
            instance_id: Jira instance ID
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issue entities
        """
        stmt = (
            select(IssueModel)
            .where(IssueModel.instance_id == instance_id)
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_project(
        self,
        instance_id: UUID,
        project_key: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IssueEntity]:
        """
        Get all issues for a project.

        Args:
            instance_id: Jira instance ID
            project_key: Project key
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issue entities
        """
        stmt = (
            select(IssueModel)
            .where(
                IssueModel.instance_id == instance_id,
                IssueModel.project_key == project_key,
            )
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_assignee(
        self,
        instance_id: UUID,
        assignee_account_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IssueEntity]:
        """
        Get all issues assigned to a user.

        Args:
            instance_id: Jira instance ID
            assignee_account_id: Assignee account ID
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issue entities
        """
        stmt = (
            select(IssueModel)
            .where(
                IssueModel.instance_id == instance_id,
                IssueModel.assignee_account_id == assignee_account_id,
            )
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_status(
        self,
        instance_id: UUID,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IssueEntity]:
        """
        Get all issues with a specific status.

        Args:
            instance_id: Jira instance ID
            status: Issue status
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issue entities
        """
        stmt = (
            select(IssueModel)
            .where(
                IssueModel.instance_id == instance_id,
                IssueModel.status == status,
            )
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_updated_since(
        self,
        instance_id: UUID,
        since: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IssueEntity]:
        """
        Get all issues updated since a specific time.

        Args:
            instance_id: Jira instance ID
            since: Timestamp to filter from
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of issue entities
        """
        stmt = (
            select(IssueModel)
            .where(
                IssueModel.instance_id == instance_id,
                IssueModel.jira_updated_at >= since,
            )
            .order_by(IssueModel.jira_updated_at)
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def search(
        self,
        instance_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[IssueEntity]:
        """
        Search issues by text query.

        Args:
            instance_id: Jira instance ID
            query: Search query
            skip: Number of issues to skip
            limit: Maximum number of issues to return

        Returns:
            List of matching issue entities
        """
        # Simple text search in summary and description
        search_pattern = f"%{query}%"
        stmt = (
            select(IssueModel)
            .where(
                IssueModel.instance_id == instance_id,
                or_(
                    IssueModel.summary.ilike(search_pattern),
                    IssueModel.description.ilike(search_pattern),
                ),
            )
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def bulk_create(self, issues: list[IssueEntity]) -> list[IssueEntity]:
        """
        Create multiple issues in bulk.

        Args:
            issues: List of issue entities to create

        Returns:
            List of created issue entities
        """
        models = [self._to_model(issue) for issue in issues]
        self.session.add_all(models)
        self.session.flush()

        for model in models:
            self.session.refresh(model)

        return [self._to_entity(model) for model in models]

    async def bulk_update(self, issues: list[IssueEntity]) -> list[IssueEntity]:
        """
        Update multiple issues in bulk.

        Args:
            issues: List of issue entities to update

        Returns:
            List of updated issue entities
        """
        models = [self._to_model(issue) for issue in issues]
        for model in models:
            self.session.merge(model)

        self.session.flush()

        for model in models:
            self.session.refresh(model)

        return [self._to_entity(model) for model in models]

    def _to_entity(self, model: IssueModel) -> IssueEntity:
        """Convert SQLAlchemy model to domain entity."""
        return IssueEntity(
            id=model.id,
            instance_id=model.instance_id,
            issue_key=model.issue_key,
            issue_id=model.issue_id,
            summary=model.summary,
            description=model.description,
            issue_type=model.issue_type,
            status=model.status,
            priority=model.priority or "Medium",
            assignee_account_id=model.assignee_account_id,
            reporter_account_id=model.reporter_account_id,
            project_key=model.project_key,
            parent_key=model.parent_key,
            labels=list(model.labels) if model.labels else [],
            components=list(model.components) if model.components else [],
            created_at=model.jira_created_at,
            updated_at=model.jira_updated_at,
            resolved_at=model.resolved_at,
            custom_fields=dict(model.custom_fields) if model.custom_fields else {},
            raw_data=dict(model.raw_jsonb) if model.raw_jsonb else {},
        )

    def _to_model(self, entity: IssueEntity) -> IssueModel:
        """Convert domain entity to SQLAlchemy model."""
        return IssueModel(
            id=entity.id,
            instance_id=entity.instance_id,
            issue_key=entity.issue_key,
            issue_id=entity.issue_id,
            summary=entity.summary,
            description=entity.description,
            issue_type=entity.issue_type,
            status=entity.status,
            priority=entity.priority,
            assignee_account_id=entity.assignee_account_id,
            reporter_account_id=entity.reporter_account_id,
            project_key=entity.project_key,
            parent_key=entity.parent_key,
            labels=entity.labels,
            components=entity.components,
            jira_created_at=entity.created_at,
            jira_updated_at=entity.updated_at,
            resolved_at=entity.resolved_at,
            custom_fields=entity.custom_fields,
            raw_jsonb=entity.raw_data,
        )


__all__ = ["IssueRepository"]

