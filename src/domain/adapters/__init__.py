"""Source adapters for multi-source support.

This package provides adapters for different issue tracking systems,
enabling Digital Spiral to work with Jira, GitHub, Asana, and other sources
through a unified interface.
"""

from .base import (
    NormalizedComment,
    NormalizedTransition,
    NormalizedWorkItem,
    SourceAdapter,
    SourceType,
    WorkItemPriority,
    WorkItemStatus,
    WorkItemType,
)
from .factory import AdapterRegistry, create_adapter
from .github_adapter import GitHubAdapter
from .jira_adapter import JiraAdapter
from .asana_adapter import AsanaAdapter
from .linear_adapter import LinearAdapter
from .clickup_adapter import ClickUpAdapter

__all__ = [
    # Base classes and enums
    "SourceAdapter",
    "SourceType",
    "WorkItemStatus",
    "WorkItemPriority",
    "WorkItemType",
    # Normalized models
    "NormalizedWorkItem",
    "NormalizedComment",
    "NormalizedTransition",
    # Adapters
    "JiraAdapter",
    "GitHubAdapter",
    "AsanaAdapter",
    "LinearAdapter",
    "ClickUpAdapter",
    # Factory
    "AdapterRegistry",
    "create_adapter",
]

