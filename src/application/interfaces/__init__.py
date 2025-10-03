"""Application layer interfaces."""

from .issue_repository import IIssueRepository
from .project_repository import IProjectRepository
from .repository import IRepository
from .user_repository import IUserRepository

__all__ = [
    "IRepository",
    "IIssueRepository",
    "IProjectRepository",
    "IUserRepository",
]