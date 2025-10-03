"""Base adapter interface for multi-source support.

This module defines the abstract base class for all source adapters,
enabling Digital Spiral to work with multiple issue tracking systems
(Jira, GitHub, Asana, etc.) through a unified interface.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class SourceType(str, Enum):
    """Supported source types."""

    JIRA = "jira"
    GITHUB = "github"
    ASANA = "asana"
    LINEAR = "linear"
    CLICKUP = "clickup"


class WorkItemStatus(str, Enum):
    """Normalized work item status."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    DONE = "done"
    CANCELLED = "cancelled"


class WorkItemPriority(str, Enum):
    """Normalized work item priority."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class WorkItemType(str, Enum):
    """Normalized work item type."""

    EPIC = "epic"
    STORY = "story"
    TASK = "task"
    BUG = "bug"
    SUBTASK = "subtask"
    FEATURE = "feature"


class NormalizedWorkItem(BaseModel):
    """Normalized work item representation across all sources."""

    # Identity
    source_id: str  # Original ID from source system
    source_key: str  # Human-readable key (e.g., PROJ-123, #456)
    source_type: SourceType
    instance_id: UUID

    # Core fields
    title: str
    description: Optional[str] = None
    status: WorkItemStatus
    priority: WorkItemPriority
    type: WorkItemType

    # Relationships
    parent_id: Optional[str] = None
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    reporter_id: Optional[str] = None

    # Metadata
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    
    # Source-specific data (stored as JSONB)
    raw_data: Dict[str, Any]
    custom_fields: Dict[str, Any] = {}

    # URLs
    url: Optional[str] = None


class NormalizedComment(BaseModel):
    """Normalized comment representation."""

    source_id: str
    work_item_id: str
    author_id: str
    body: str
    created_at: datetime
    updated_at: datetime
    raw_data: Dict[str, Any]


class NormalizedTransition(BaseModel):
    """Normalized status transition."""

    work_item_id: str
    from_status: WorkItemStatus
    to_status: WorkItemStatus
    actor_id: str
    timestamp: datetime
    raw_data: Dict[str, Any]


class SourceAdapter(ABC):
    """Abstract base class for source adapters.

    Each source adapter implements this interface to provide
    a unified way to interact with different issue tracking systems.
    """

    def __init__(
        self,
        instance_id: UUID,
        base_url: str,
        auth_config: Dict[str, Any],
    ):
        """Initialize the adapter.

        Args:
            instance_id: Unique identifier for this source instance
            base_url: Base URL for the source API
            auth_config: Authentication configuration (API key, OAuth, etc.)
        """
        self.instance_id = instance_id
        self.base_url = base_url
        self.auth_config = auth_config

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the source.

        Returns:
            True if connection is successful, False otherwise
        """
        pass

    @abstractmethod
    async def fetch_work_items(
        self,
        project_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[NormalizedWorkItem]:
        """Fetch work items from the source.

        Args:
            project_id: Optional project/repository ID to filter by
            updated_since: Only fetch items updated after this time
            limit: Maximum number of items to fetch

        Returns:
            List of normalized work items
        """
        pass

    @abstractmethod
    async def fetch_work_item(self, work_item_id: str) -> NormalizedWorkItem:
        """Fetch a single work item by ID.

        Args:
            work_item_id: Source-specific work item ID

        Returns:
            Normalized work item
        """
        pass

    @abstractmethod
    async def create_work_item(
        self,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        type: WorkItemType = WorkItemType.TASK,
        priority: WorkItemPriority = WorkItemPriority.MEDIUM,
        assignee_id: Optional[str] = None,
        **kwargs,
    ) -> NormalizedWorkItem:
        """Create a new work item.

        Args:
            project_id: Project/repository ID
            title: Work item title
            description: Work item description
            type: Work item type
            priority: Work item priority
            assignee_id: Assignee user ID
            **kwargs: Source-specific additional fields

        Returns:
            Created work item
        """
        pass

    @abstractmethod
    async def update_work_item(
        self,
        work_item_id: str,
        **fields,
    ) -> NormalizedWorkItem:
        """Update a work item.

        Args:
            work_item_id: Work item ID
            **fields: Fields to update

        Returns:
            Updated work item
        """
        pass

    @abstractmethod
    async def transition_work_item(
        self,
        work_item_id: str,
        to_status: WorkItemStatus,
        comment: Optional[str] = None,
    ) -> NormalizedWorkItem:
        """Transition a work item to a new status.

        Args:
            work_item_id: Work item ID
            to_status: Target status
            comment: Optional comment

        Returns:
            Updated work item
        """
        pass

    @abstractmethod
    async def add_comment(
        self,
        work_item_id: str,
        body: str,
    ) -> NormalizedComment:
        """Add a comment to a work item.

        Args:
            work_item_id: Work item ID
            body: Comment body

        Returns:
            Created comment
        """
        pass

    @abstractmethod
    async def fetch_comments(
        self,
        work_item_id: str,
    ) -> List[NormalizedComment]:
        """Fetch comments for a work item.

        Args:
            work_item_id: Work item ID

        Returns:
            List of comments
        """
        pass

    @abstractmethod
    async def fetch_transitions(
        self,
        work_item_id: str,
    ) -> List[NormalizedTransition]:
        """Fetch status transitions for a work item.

        Args:
            work_item_id: Work item ID

        Returns:
            List of transitions
        """
        pass

    @abstractmethod
    def normalize_status(self, source_status: str) -> WorkItemStatus:
        """Normalize source-specific status to standard status.

        Args:
            source_status: Source-specific status string

        Returns:
            Normalized status
        """
        pass

    @abstractmethod
    def normalize_priority(self, source_priority: str) -> WorkItemPriority:
        """Normalize source-specific priority to standard priority.

        Args:
            source_priority: Source-specific priority string

        Returns:
            Normalized priority
        """
        pass

    @abstractmethod
    def normalize_type(self, source_type: str) -> WorkItemType:
        """Normalize source-specific type to standard type.

        Args:
            source_type: Source-specific type string

        Returns:
            Normalized type
        """
        pass


__all__ = [
    "SourceType",
    "WorkItemStatus",
    "WorkItemPriority",
    "WorkItemType",
    "NormalizedWorkItem",
    "NormalizedComment",
    "NormalizedTransition",
    "SourceAdapter",
]

