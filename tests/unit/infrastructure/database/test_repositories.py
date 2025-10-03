"""Unit tests for repository implementations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.entities import Issue, Project, User
from src.infrastructure.database.models import Base
from src.infrastructure.database.models import Issue as IssueModel
from src.infrastructure.database.models import Project as ProjectModel
from src.infrastructure.database.models import User as UserModel
from src.infrastructure.database.repositories import (
    IssueRepository,
    ProjectRepository,
    UserRepository,
)


@pytest.fixture
def engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def instance_id():
    """Create a test instance ID."""
    return uuid.uuid4()


@pytest.fixture
def tenant_id():
    """Create a test tenant ID."""
    return uuid.uuid4()


class TestIssueRepository:
    """Tests for IssueRepository."""

    @pytest.mark.asyncio
    async def test_create_issue(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test creating an issue."""
        repo = IssueRepository(session)

        issue = Issue(
            id=uuid.uuid4(),
            instance_id=instance_id,
            issue_key="PROJ-1",
            issue_id="10001",
            summary="Test issue",
            project_key="PROJ",
        )

        # Convert to model and add tenant_id
        model = repo._to_model(issue)
        model.tenant_id = tenant_id

        session.add(model)
        session.commit()

        # Retrieve and verify
        retrieved = await repo.get_by_key("PROJ-1")
        assert retrieved is not None
        assert retrieved.issue_key == "PROJ-1"
        assert retrieved.summary == "Test issue"

    @pytest.mark.asyncio
    async def test_get_by_instance(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test getting issues by instance."""
        repo = IssueRepository(session)

        # Create multiple issues
        for i in range(3):
            issue = Issue(
                id=uuid.uuid4(),
                instance_id=instance_id,
                issue_key=f"PROJ-{i}",
                issue_id=f"1000{i}",
                summary=f"Issue {i}",
                project_key="PROJ",
            )
            model = repo._to_model(issue)
            model.tenant_id = tenant_id
            session.add(model)

        session.commit()

        # Retrieve all issues for instance
        issues = await repo.get_by_instance(instance_id)
        assert len(issues) == 3

    @pytest.mark.asyncio
    async def test_get_by_project(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test getting issues by project."""
        repo = IssueRepository(session)

        # Create issues for different projects
        for project_key in ["PROJ", "OTHER"]:
            for i in range(2):
                issue = Issue(
                    id=uuid.uuid4(),
                    instance_id=instance_id,
                    issue_key=f"{project_key}-{i}",
                    issue_id=f"{project_key}-1000{i}",
                    summary=f"Issue {i}",
                    project_key=project_key,
                )
                model = repo._to_model(issue)
                model.tenant_id = tenant_id
                session.add(model)

        session.commit()

        # Retrieve issues for PROJ
        issues = await repo.get_by_project(instance_id, "PROJ")
        assert len(issues) == 2
        assert all(issue.project_key == "PROJ" for issue in issues)

    @pytest.mark.asyncio
    async def test_search_issues(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test searching issues."""
        repo = IssueRepository(session)

        # Create issues with different summaries
        summaries = ["Fix login bug", "Add new feature", "Update documentation"]
        for i, summary in enumerate(summaries):
            issue = Issue(
                id=uuid.uuid4(),
                instance_id=instance_id,
                issue_key=f"PROJ-{i}",
                issue_id=f"1000{i}",
                summary=summary,
                project_key="PROJ",
            )
            model = repo._to_model(issue)
            model.tenant_id = tenant_id
            session.add(model)

        session.commit()

        # Search for "bug"
        issues = await repo.search(instance_id, "bug")
        assert len(issues) == 1
        assert issues[0].summary == "Fix login bug"


class TestProjectRepository:
    """Tests for ProjectRepository."""

    @pytest.mark.asyncio
    async def test_create_project(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test creating a project."""
        repo = ProjectRepository(session)

        project = Project(
            id=uuid.uuid4(),
            instance_id=instance_id,
            project_key="PROJ",
            project_id="10000",
            name="Test Project",
        )

        # Convert to model and add tenant_id
        model = repo._to_model(project)
        model.tenant_id = tenant_id

        session.add(model)
        session.commit()

        # Retrieve and verify
        retrieved = await repo.get_by_key(instance_id, "PROJ")
        assert retrieved is not None
        assert retrieved.project_key == "PROJ"
        assert retrieved.name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_active_projects(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test getting active projects."""
        repo = ProjectRepository(session)

        # Create active and archived projects
        for i in range(3):
            project = Project(
                id=uuid.uuid4(),
                instance_id=instance_id,
                project_key=f"PROJ{i}",
                project_id=f"1000{i}",
                name=f"Project {i}",
                is_archived=(i == 2),  # Last one is archived
            )
            model = repo._to_model(project)
            model.tenant_id = tenant_id
            session.add(model)

        session.commit()

        # Retrieve active projects
        projects = await repo.get_active(instance_id)
        assert len(projects) == 2
        assert all(not project.is_archived for project in projects)


class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.mark.asyncio
    async def test_create_user(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test creating a user."""
        repo = UserRepository(session)

        user = User(
            id=uuid.uuid4(),
            instance_id=instance_id,
            account_id="account123",
            display_name="John Doe",
            email_address="john@example.com",
        )

        # Convert to model and add tenant_id
        model = repo._to_model(user)
        model.tenant_id = tenant_id

        session.add(model)
        session.commit()

        # Retrieve and verify
        retrieved = await repo.get_by_account_id(instance_id, "account123")
        assert retrieved is not None
        assert retrieved.account_id == "account123"
        assert retrieved.display_name == "John Doe"

    @pytest.mark.asyncio
    async def test_search_by_email(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test searching user by email."""
        repo = UserRepository(session)

        user = User(
            id=uuid.uuid4(),
            instance_id=instance_id,
            account_id="account123",
            display_name="John Doe",
            email_address="john@example.com",
        )

        model = repo._to_model(user)
        model.tenant_id = tenant_id

        session.add(model)
        session.commit()

        # Search by email
        retrieved = await repo.search_by_email(instance_id, "john@example.com")
        assert retrieved is not None
        assert retrieved.email_address == "john@example.com"

    @pytest.mark.asyncio
    async def test_get_active_users(self, session: Session, instance_id: uuid.UUID, tenant_id: uuid.UUID):
        """Test getting active users."""
        repo = UserRepository(session)

        # Create active and inactive users
        for i in range(3):
            user = User(
                id=uuid.uuid4(),
                instance_id=instance_id,
                account_id=f"account{i}",
                display_name=f"User {i}",
                is_active=(i != 2),  # Last one is inactive
            )
            model = repo._to_model(user)
            model.tenant_id = tenant_id
            session.add(model)

        session.commit()

        # Retrieve active users
        users = await repo.get_active(instance_id)
        assert len(users) == 2
        assert all(user.is_active for user in users)

