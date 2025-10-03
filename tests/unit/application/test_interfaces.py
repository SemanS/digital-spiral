"""Unit tests for application interfaces."""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from src.application.interfaces import (
    IIssueRepository,
    IProjectRepository,
    IRepository,
    IUserRepository,
)
from src.domain.entities import Issue, Project, User


class MockRepository(IRepository[Issue]):
    """Mock repository for testing."""

    def __init__(self):
        self.storage: dict[uuid.UUID, Issue] = {}

    async def get_by_id(self, id: uuid.UUID) -> Issue | None:
        return self.storage.get(id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Issue]:
        items = list(self.storage.values())
        return items[skip : skip + limit]

    async def create(self, entity: Issue) -> Issue:
        self.storage[entity.id] = entity
        return entity

    async def update(self, entity: Issue) -> Issue:
        self.storage[entity.id] = entity
        return entity

    async def delete(self, id: uuid.UUID) -> bool:
        if id in self.storage:
            del self.storage[id]
            return True
        return False

    async def exists(self, id: uuid.UUID) -> bool:
        return id in self.storage

    async def count(self) -> int:
        return len(self.storage)


class TestIRepository:
    """Tests for IRepository interface."""

    @pytest.mark.asyncio
    async def test_create_and_get(self):
        """Test creating and getting an entity."""
        repo = MockRepository()

        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-1",
            issue_id="10001",
            summary="Test issue",
        )

        created = await repo.create(issue)
        assert created.id == issue.id

        retrieved = await repo.get_by_id(issue.id)
        assert retrieved is not None
        assert retrieved.id == issue.id
        assert retrieved.summary == "Test issue"

    @pytest.mark.asyncio
    async def test_get_all(self):
        """Test getting all entities."""
        repo = MockRepository()

        # Create multiple issues
        for i in range(5):
            issue = Issue(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                issue_key=f"PROJ-{i}",
                issue_id=f"1000{i}",
                summary=f"Issue {i}",
            )
            await repo.create(issue)

        all_issues = await repo.get_all()
        assert len(all_issues) == 5

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self):
        """Test getting all entities with pagination."""
        repo = MockRepository()

        # Create 10 issues
        for i in range(10):
            issue = Issue(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                issue_key=f"PROJ-{i}",
                issue_id=f"1000{i}",
                summary=f"Issue {i}",
            )
            await repo.create(issue)

        # Get first page
        page1 = await repo.get_all(skip=0, limit=5)
        assert len(page1) == 5

        # Get second page
        page2 = await repo.get_all(skip=5, limit=5)
        assert len(page2) == 5

    @pytest.mark.asyncio
    async def test_update(self):
        """Test updating an entity."""
        repo = MockRepository()

        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-1",
            issue_id="10001",
            summary="Original summary",
        )

        await repo.create(issue)

        # Update summary
        issue.summary = "Updated summary"
        updated = await repo.update(issue)

        assert updated.summary == "Updated summary"

        # Verify update persisted
        retrieved = await repo.get_by_id(issue.id)
        assert retrieved.summary == "Updated summary"

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test deleting an entity."""
        repo = MockRepository()

        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-1",
            issue_id="10001",
            summary="Test issue",
        )

        await repo.create(issue)
        assert await repo.exists(issue.id) is True

        deleted = await repo.delete(issue.id)
        assert deleted is True
        assert await repo.exists(issue.id) is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self):
        """Test deleting a non-existent entity."""
        repo = MockRepository()

        deleted = await repo.delete(uuid.uuid4())
        assert deleted is False

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking if entity exists."""
        repo = MockRepository()

        issue = Issue(
            id=uuid.uuid4(),
            instance_id=uuid.uuid4(),
            issue_key="PROJ-1",
            issue_id="10001",
            summary="Test issue",
        )

        assert await repo.exists(issue.id) is False

        await repo.create(issue)
        assert await repo.exists(issue.id) is True

    @pytest.mark.asyncio
    async def test_count(self):
        """Test counting entities."""
        repo = MockRepository()

        assert await repo.count() == 0

        # Create 3 issues
        for i in range(3):
            issue = Issue(
                id=uuid.uuid4(),
                instance_id=uuid.uuid4(),
                issue_key=f"PROJ-{i}",
                issue_id=f"1000{i}",
                summary=f"Issue {i}",
            )
            await repo.create(issue)

        assert await repo.count() == 3


class TestRepositoryInterfaces:
    """Tests for repository interface definitions."""

    def test_issue_repository_interface(self):
        """Test that IIssueRepository extends IRepository."""
        assert issubclass(IIssueRepository, IRepository)

    def test_project_repository_interface(self):
        """Test that IProjectRepository extends IRepository."""
        assert issubclass(IProjectRepository, IRepository)

    def test_user_repository_interface(self):
        """Test that IUserRepository extends IRepository."""
        assert issubclass(IUserRepository, IRepository)

    def test_issue_repository_has_specific_methods(self):
        """Test that IIssueRepository has issue-specific methods."""
        methods = [
            "get_by_key",
            "get_by_instance",
            "get_by_project",
            "get_by_assignee",
            "get_by_status",
            "get_updated_since",
            "search",
            "bulk_create",
            "bulk_update",
        ]

        for method in methods:
            assert hasattr(IIssueRepository, method)

    def test_project_repository_has_specific_methods(self):
        """Test that IProjectRepository has project-specific methods."""
        methods = [
            "get_by_key",
            "get_by_instance",
            "get_active",
        ]

        for method in methods:
            assert hasattr(IProjectRepository, method)

    def test_user_repository_has_specific_methods(self):
        """Test that IUserRepository has user-specific methods."""
        methods = [
            "get_by_account_id",
            "get_by_instance",
            "get_active",
            "search_by_email",
        ]

        for method in methods:
            assert hasattr(IUserRepository, method)

