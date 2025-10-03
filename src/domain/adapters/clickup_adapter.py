"""ClickUp adapter implementation."""

import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

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


class ClickUpAdapter(SourceAdapter):
    """Adapter for ClickUp."""

    # Status mapping from ClickUp to normalized
    STATUS_MAP = {
        "to do": WorkItemStatus.TODO,
        "open": WorkItemStatus.TODO,
        "in progress": WorkItemStatus.IN_PROGRESS,
        "blocked": WorkItemStatus.BLOCKED,
        "review": WorkItemStatus.IN_REVIEW,
        "closed": WorkItemStatus.DONE,
        "complete": WorkItemStatus.DONE,
        "cancelled": WorkItemStatus.CANCELLED,
    }

    # Priority mapping (ClickUp uses 1-4, where 1 is urgent)
    PRIORITY_MAP = {
        "urgent": WorkItemPriority.CRITICAL,
        "high": WorkItemPriority.HIGH,
        "normal": WorkItemPriority.MEDIUM,
        "low": WorkItemPriority.LOW,
    }

    # Type mapping (ClickUp doesn't have built-in types, use tags)
    TYPE_MAP = {
        "epic": WorkItemType.EPIC,
        "story": WorkItemType.STORY,
        "task": WorkItemType.TASK,
        "bug": WorkItemType.BUG,
        "feature": WorkItemType.FEATURE,
    }

    def __init__(
        self,
        instance_id: UUID,
        base_url: str,
        auth_config: Dict[str, Any],
    ):
        """Initialize ClickUp adapter.

        Args:
            instance_id: Instance UUID
            base_url: ClickUp API base URL (default: https://api.clickup.com/api/v2)
            auth_config: Dict with 'api_token' (ClickUp API token)
        """
        super().__init__(instance_id, base_url, auth_config)
        self.client = httpx.AsyncClient(
            base_url=base_url or "https://api.clickup.com/api/v2",
            headers={
                "Authorization": auth_config['api_token'],
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def test_connection(self) -> bool:
        """Test connection to ClickUp."""
        try:
            response = await self.client.get("/user")
            return response.status_code == 200
        except Exception:
            return False

    async def fetch_work_items(
        self,
        project_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[NormalizedWorkItem]:
        """Fetch tasks from ClickUp.

        Args:
            project_id: ClickUp list ID
            updated_since: Only fetch items updated after this time
            limit: Maximum number of items to fetch
        """
        if not project_id:
            raise ValueError("project_id (ClickUp list ID) is required")
        
        params = {
            "archived": "false",
            "page": 0,
        }
        
        if updated_since:
            params["date_updated_gt"] = int(updated_since.timestamp() * 1000)
        
        response = await self.client.get(f"/list/{project_id}/task", params=params)
        response.raise_for_status()
        
        data = response.json()
        tasks = data.get("tasks", [])[:limit]
        
        return [self._normalize_task(task, project_id) for task in tasks]

    async def fetch_work_item(self, work_item_id: str) -> NormalizedWorkItem:
        """Fetch a single ClickUp task.

        Args:
            work_item_id: ClickUp task ID
        """
        response = await self.client.get(f"/task/{work_item_id}")
        response.raise_for_status()
        
        task = response.json()
        list_id = task.get("list", {}).get("id", "")
        return self._normalize_task(task, list_id)

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
        """Create a new ClickUp task."""
        payload = {
            "name": title,
            "description": description or "",
            "priority": self._denormalize_priority(priority),
        }
        
        if assignee_id:
            payload["assignees"] = [assignee_id]
        
        # Add tags for type
        tags = [self._denormalize_type(type)]
        if "tags" in kwargs:
            tags.extend(kwargs["tags"])
        payload["tags"] = tags
        
        response = await self.client.post(f"/list/{project_id}/task", json=payload)
        response.raise_for_status()
        
        created = response.json()
        return await self.fetch_work_item(created["id"])

    async def update_work_item(
        self,
        work_item_id: str,
        **fields,
    ) -> NormalizedWorkItem:
        """Update a ClickUp task."""
        response = await self.client.put(f"/task/{work_item_id}", json=fields)
        response.raise_for_status()
        
        return await self.fetch_work_item(work_item_id)

    async def transition_work_item(
        self,
        work_item_id: str,
        to_status: WorkItemStatus,
        comment: Optional[str] = None,
    ) -> NormalizedWorkItem:
        """Transition a ClickUp task.

        Note: ClickUp requires status ID, which varies by space.
        This is a simplified implementation.
        """
        # Get task to find current status
        task = await self.fetch_work_item(work_item_id)
        
        # In production, you'd need to:
        # 1. Get available statuses for the list
        # 2. Find the status ID that matches to_status
        # 3. Update the task with that status ID
        
        # For now, we'll just update the status field
        status_name = self._denormalize_status(to_status)
        
        payload = {"status": status_name}
        response = await self.client.put(f"/task/{work_item_id}", json=payload)
        response.raise_for_status()
        
        if comment:
            await self.add_comment(work_item_id, comment)
        
        return await self.fetch_work_item(work_item_id)

    async def add_comment(
        self,
        work_item_id: str,
        body: str,
    ) -> NormalizedComment:
        """Add a comment to a ClickUp task."""
        payload = {
            "comment_text": body,
        }
        
        response = await self.client.post(
            f"/task/{work_item_id}/comment",
            json=payload,
        )
        response.raise_for_status()
        
        comment = response.json()
        return self._normalize_comment(comment, work_item_id)

    async def fetch_comments(
        self,
        work_item_id: str,
    ) -> List[NormalizedComment]:
        """Fetch comments for a ClickUp task."""
        response = await self.client.get(f"/task/{work_item_id}/comment")
        response.raise_for_status()
        
        data = response.json()
        comments = data.get("comments", [])
        
        return [
            self._normalize_comment(comment, work_item_id)
            for comment in comments
        ]

    async def fetch_transitions(
        self,
        work_item_id: str,
    ) -> List[NormalizedTransition]:
        """Fetch transitions for a ClickUp task.

        ClickUp doesn't provide transition history directly.
        Would need to parse task history/activity.
        """
        return []

    def normalize_status(self, source_status: str) -> WorkItemStatus:
        """Normalize ClickUp status."""
        return self.STATUS_MAP.get(source_status.lower(), WorkItemStatus.TODO)

    def normalize_priority(self, source_priority: str) -> WorkItemPriority:
        """Normalize ClickUp priority."""
        return self.PRIORITY_MAP.get(source_priority.lower(), WorkItemPriority.MEDIUM)

    def normalize_type(self, source_type: str) -> WorkItemType:
        """Normalize ClickUp type."""
        return self.TYPE_MAP.get(source_type.lower(), WorkItemType.TASK)

    def _denormalize_status(self, status: WorkItemStatus) -> str:
        """Convert normalized status to ClickUp status."""
        reverse_map = {v: k for k, v in self.STATUS_MAP.items()}
        return reverse_map.get(status, "to do")

    def _denormalize_priority(self, priority: WorkItemPriority) -> int:
        """Convert normalized priority to ClickUp priority (1-4)."""
        priority_map = {
            WorkItemPriority.CRITICAL: 1,
            WorkItemPriority.HIGH: 2,
            WorkItemPriority.MEDIUM: 3,
            WorkItemPriority.LOW: 4,
            WorkItemPriority.NONE: 3,
        }
        return priority_map.get(priority, 3)

    def _denormalize_type(self, type: WorkItemType) -> str:
        """Convert normalized type to ClickUp tag."""
        reverse_map = {v: k for k, v in self.TYPE_MAP.items()}
        return reverse_map.get(type, "task")

    def _normalize_task(
        self,
        task: Dict[str, Any],
        project_id: str,
    ) -> NormalizedWorkItem:
        """Normalize a ClickUp task to standard format."""
        # Extract tags
        tags = [tag["name"].lower() for tag in task.get("tags", [])]
        
        # Determine type from tags
        type = WorkItemType.TASK
        for tag in tags:
            if tag in self.TYPE_MAP:
                type = self.TYPE_MAP[tag]
                break
        
        # Map priority (ClickUp uses 1-4)
        priority_value = task.get("priority")
        if priority_value:
            priority_name = priority_value.get("priority", "normal").lower()
            priority = self.normalize_priority(priority_name)
        else:
            priority = WorkItemPriority.MEDIUM
        
        # Get assignees
        assignees = task.get("assignees", [])
        assignee_id = assignees[0]["id"] if assignees else None
        
        return NormalizedWorkItem(
            source_id=task["id"],
            source_key=task.get("custom_id") or task["id"],
            source_type=SourceType.CLICKUP,
            instance_id=self.instance_id,
            title=task.get("name", ""),
            description=task.get("description"),
            status=self.normalize_status(task.get("status", {}).get("status", "")),
            priority=priority,
            type=type,
            parent_id=task.get("parent"),
            project_id=project_id,
            assignee_id=assignee_id,
            reporter_id=task.get("creator", {}).get("id"),
            created_at=datetime.fromtimestamp(int(task["date_created"]) / 1000),
            updated_at=datetime.fromtimestamp(int(task["date_updated"]) / 1000),
            closed_at=datetime.fromtimestamp(int(task["date_closed"]) / 1000) if task.get("date_closed") else None,
            raw_data=task,
            custom_fields={
                "tags": tags,
                "time_estimate": task.get("time_estimate"),
                "time_spent": task.get("time_spent"),
            },
            url=task.get("url"),
        )

    def _normalize_comment(
        self,
        comment: Dict[str, Any],
        work_item_id: str,
    ) -> NormalizedComment:
        """Normalize a ClickUp comment."""
        return NormalizedComment(
            source_id=comment["id"],
            work_item_id=work_item_id,
            author_id=comment.get("user", {}).get("id", ""),
            body=comment.get("comment_text", ""),
            created_at=datetime.fromtimestamp(int(comment["date"]) / 1000),
            updated_at=datetime.fromtimestamp(int(comment["date"]) / 1000),
            raw_data=comment,
        )


__all__ = ["ClickUpAdapter"]

