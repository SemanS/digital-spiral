"""Dependency injection for FastAPI."""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.services import IssueService, SyncService
from src.application.use_cases import (
    FullSyncUseCase,
    GetIssueByKeyUseCase,
    GetIssuesByProjectUseCase,
    GetIssueUseCase,
    GetSyncStatusUseCase,
    IncrementalSyncUseCase,
    SearchIssuesUseCase,
    SyncIssueUseCase,
)
from src.infrastructure.database.repositories import IssueRepository
from src.infrastructure.external.jira import JiraClient

logger = logging.getLogger(__name__)

# Database configuration
# TODO: Load from environment variables
DATABASE_URL = "postgresql+asyncpg://digital_spiral:digital_spiral@localhost:5432/digital_spiral"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create session factory
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.

    Yields:
        Database session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_jira_client() -> JiraClient:
    """
    Get Jira API client.

    Returns:
        Jira client

    Note:
        This is a placeholder. In production, you would:
        1. Get credentials from database based on instance_id
        2. Use OAuth tokens from user session
        3. Cache clients per instance
    """
    # TODO: Implement proper client creation based on instance
    return JiraClient(
        base_url="https://your-domain.atlassian.net",
        email="your-email@example.com",
        api_token="your-api-token",
    )


async def get_issue_repository(
    session: AsyncSession = None,
) -> IssueRepository:
    """
    Get issue repository.

    Args:
        session: Database session

    Returns:
        Issue repository
    """
    if session is None:
        async for session in get_db_session():
            return IssueRepository(session)
    return IssueRepository(session)


async def get_issue_service() -> IssueService:
    """
    Get issue service.

    Returns:
        Issue service
    """
    # Get dependencies
    async for session in get_db_session():
        issue_repository = IssueRepository(session)
        jira_client = await get_jira_client()

        # Create use cases
        get_issue_use_case = GetIssueUseCase(issue_repository)
        get_issue_by_key_use_case = GetIssueByKeyUseCase(issue_repository)
        search_issues_use_case = SearchIssuesUseCase(issue_repository)
        sync_issue_use_case = SyncIssueUseCase(issue_repository, jira_client)
        get_issues_by_project_use_case = GetIssuesByProjectUseCase(issue_repository)

        # Create service
        return IssueService(
            get_issue_use_case=get_issue_use_case,
            get_issue_by_key_use_case=get_issue_by_key_use_case,
            search_issues_use_case=search_issues_use_case,
            sync_issue_use_case=sync_issue_use_case,
            get_issues_by_project_use_case=get_issues_by_project_use_case,
        )


async def get_sync_service() -> SyncService:
    """
    Get sync service.

    Returns:
        Sync service
    """
    # Get dependencies
    jira_client = await get_jira_client()

    # Create use cases
    full_sync_use_case = FullSyncUseCase(jira_client)
    incremental_sync_use_case = IncrementalSyncUseCase(jira_client)
    get_sync_status_use_case = GetSyncStatusUseCase()

    # Create service
    return SyncService(
        full_sync_use_case=full_sync_use_case,
        incremental_sync_use_case=incremental_sync_use_case,
        get_sync_status_use_case=get_sync_status_use_case,
    )


__all__ = [
    "get_db_session",
    "get_jira_client",
    "get_issue_repository",
    "get_issue_service",
    "get_sync_service",
]

