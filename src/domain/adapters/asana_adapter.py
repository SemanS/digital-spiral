"""Asana adapter implementation."""

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


class AsanaAdapter(SourceAdapter):
    """Adapter for Asana."""

    # Status mapping from Asana to normalized
    STATUS_MAP = {
        "incomplete": WorkItemStatus.TODO,
        "in_progress": WorkItemStatus.IN_PROGRESS,
        "complete": WorkItemStatus.DONE,
    }

    # Priority mapping (Asana doesn't have built-in priority, use custom fields)
    PRIORITY_MAP = {
        "critical": WorkItemPriority.CRITICAL,
        "high": WorkItemPriority.HIGH,
        "medium": WorkItemPriority.MEDIUM,
        "low": WorkItemPriority.LOW,
    }

    # Type mapping (from custom fields or tags)
    TYPE_MAP = {
        "epic": WorkItemType.EPIC,
        "story": WorkItemType.STORY,
        "task": WorkItemType.TASK,
        "bug": WorkItemType.BUG,
        "subtask": WorkItemType.SUBTASK,
        "feature": WorkItemType.FEATURE,
    }

    def __init__(
        self,
        instance_id: UUID,
        base_url: str,
        auth_config: Dict[str, Any],
    ):
        """Initialize Asana adapter.

        Args:
            instance_id: Instance UUID
            base_url: Asana API base URL (default: https://app.asana.com/api/1.0)
            auth_config: Dict with 'access_token' (personal access token)
        """
        super().__init__(instance_id, base_url, auth_config)
        self.client = httpx.AsyncClient(
            base_url=base_url or "https://app.asana.com/api/1.0",
            headers={
                "Authorization": f"Bearer {auth_config['access_token']}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def test_connection(self) -> bool:
        """Test connection to Asana."""
        try:
            response = await self.client.get("/users/me")
            return response.status_code == 200
        except Exception:
            return False

    async def fetch_work_items(
        self,
        project_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[NormalizedWorkItem]:
        """Fetch tasks from Asana.

        Args:
            project_id: Asana project GID
            updated_since: Only fetch items updated after this time
            limit: Maximum number of items to fetch
        """
        if not project_id:
            raise ValueError("project_id (Asana project GID) is required")
        
        params = {
            "project": project_id,
            "limit": min(limit, 100),
            "opt_fields": "name,notes,completed,due_on,assignee,created_at,modified_at,parent,custom_fields,tags",
        }
        
        if updated_since:
            params["modified_since"] = updated_since.isoformat()
        
        response = await self.client.get("/tasks", params=params)
        response.raise_for_status()
        
        data = response.json()
        tasks = data.get("data", [])
        
        # Fetch full details for each task
        normalized_tasks = []
        for task in tasks:
            full_task = await self._fetch_task_details(task["gid"])
            normalized_tasks.append(self._normalize_task(full_task, project_id))
        
        return normalized_tasks

    async def fetch_work_item(self, work_item_id: str) -> NormalizedWorkItem:
        """Fetch a single Asana task.

        Args:
            work_item_id: Asana task GID
        """
        task = await self._fetch_task_details(work_item_id)
        project_id = task.get("projects", [{}])[0].get("gid", "")
        return self._normalize_task(task, project_id)

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
        """Create a new Asana task."""
        payload = {
            "data": {
                "name": title,
                "notes": description or "",
                "projects": [project_id],
            }
        }
        
        if assignee_id:
            payload["data"]["assignee"] = assignee_id
        
        # Add custom fields for priority and type
        # Note: This requires knowing the custom field GIDs for the project
        # In production, you'd fetch these from the project settings
        
        response = await self.client.post("/tasks", json=payload)
        response.raise_for_status()
        
        created = response.json()["data"]
        return await self.fetch_work_item(created["gid"])

    async def update_work_item(
        self,
        work_item_id: str,
        **fields,
    ) -> NormalizedWorkItem:
        """Update an Asana task."""
        payload = {"data": fields}
        
        response = await self.client.put(f"/tasks/{work_item_id}", json=payload)
        response.raise_for_status()
        
        return await self.fetch_work_item(work_item_id)

    async def transition_work_item(
        self,
        work_item_id: str,
        to_status: WorkItemStatus,
        comment: Optional[str] = None,
    ) -> NormalizedWorkItem:
        """Transition an Asana task.

        Asana uses 'completed' boolean, so we map:
        - DONE -> completed: true
        - Others -> completed: false
        """
        completed = to_status == WorkItemStatus.DONE
        
        payload = {"data": {"completed": completed}}
        
        response = await self.client.put(f"/tasks/{work_item_id}", json=payload)
        response.raise_for_status()
        
        # Add comment if provided
        if comment:
            await self.add_comment(work_item_id, comment)
        
        return await self.fetch_work_item(work_item_id)

    async def add_comment(
        self,
        work_item_id: str,
        body: str,
    ) -> NormalizedComment:
        """Add a comment (story) to an Asana task."""
        payload = {
            "data": {
                "text": body,
            }
        }
        
        response = await self.client.post(
            f"/tasks/{work_item_id}/stories",
            json=payload,
        )
        response.raise_for_status()
        
        story = response.json()["data"]
        return self._normalize_story(story, work_item_id)

    async def fetch_comments(
        self,
        work_item_id: str,
    ) -> List[NormalizedComment]:
        """Fetch comments (stories) for an Asana task."""
        response = await self.client.get(f"/tasks/{work_item_id}/stories")
        response.raise_for_status()
        
        stories = response.json()["data"]
        
        # Filter to only comment stories (not system events)
        return [
            self._normalize_story(story, work_item_id)
            for story in stories
            if story.get("type") == "comment"
        ]

    async def fetch_transitions(
        self,
        work_item_id: str,
    ) -> List[NormalizedTransition]:
        """Fetch transitions for an Asana task.

        Asana doesn't have explicit transitions, so we parse stories
        for completion events.
        """
        response = await self.client.get(f"/tasks/{work_item_id}/stories")
        response.raise_for_status()
        
        stories = response.json()["data"]
        transitions = []
        
        for story in stories:
            if story.get("type") == "system":
                text = story.get("text", "")
                if "completed" in text.lower():
                    transitions.append(
                        NormalizedTransition(
                            work_item_id=work_item_id,
                            from_status=WorkItemStatus.TODO,
                            to_status=WorkItemStatus.DONE,
                            actor_id=story.get("created_by", {}).get("gid", ""),
                            timestamp=datetime.fromisoformat(
                                story.get("created_at", "").replace("Z", "+00:00")
                            ),
                            raw_data=story,
                        )
                    )
        
        return transitions

    def normalize_status(self, source_status: str) -> WorkItemStatus:
        """Normalize Asana status."""
        return self.STATUS_MAP.get(source_status.lower(), WorkItemStatus.TODO)

    def normalize_priority(self, source_priority: str) -> WorkItemPriority:
        """Normalize Asana priority."""
        return self.PRIORITY_MAP.get(source_priority.lower(), WorkItemPriority.MEDIUM)

    def normalize_type(self, source_type: str) -> WorkItemType:
        """Normalize Asana type."""
        return self.TYPE_MAP.get(source_type.lower(), WorkItemType.TASK)

    async def _fetch_task_details(self, task_gid: str) -> Dict[str, Any]:
        """Fetch full task details."""
        response = await self.client.get(
            f"/tasks/{task_gid}",
            params={
                "opt_fields": "name,notes,completed,due_on,assignee,created_at,modified_at,parent,custom_fields,tags,projects,permalink_url",
            },
        )
        response.raise_for_status()
        return response.json()["data"]

    def _normalize_task(
        self,
        task: Dict[str, Any],
        project_id: str,
    ) -> NormalizedWorkItem:
        """Normalize an Asana task to standard format."""
        # Determine status
        status = WorkItemStatus.DONE if task.get("completed") else WorkItemStatus.TODO
        
        # Extract priority and type from custom fields or tags
        priority = WorkItemPriority.MEDIUM
        type = WorkItemType.TASK
        
        for tag in task.get("tags", []):
            tag_name = tag.get("name", "").lower()
            if tag_name in self.PRIORITY_MAP:
                priority = self.PRIORITY_MAP[tag_name]
            if tag_name in self.TYPE_MAP:
                type = self.TYPE_MAP[tag_name]
        
        return NormalizedWorkItem(
            source_id=task["gid"],
            source_key=task["gid"],  # Asana doesn't have human-readable keys
            source_type=SourceType.ASANA,
            instance_id=self.instance_id,
            title=task.get("name", ""),
            description=task.get("notes"),
            status=status,
            priority=priority,
            type=type,
            parent_id=task.get("parent", {}).get("gid") if task.get("parent") else None,
            project_id=project_id,
            assignee_id=task.get("assignee", {}).get("gid") if task.get("assignee") else None,
            reporter_id=None,  # Asana doesn't have a reporter field
            created_at=datetime.fromisoformat(
                task.get("created_at", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                task.get("modified_at", "").replace("Z", "+00:00")
            ),
            closed_at=None,  # Asana doesn't track completion time
            raw_data=task,
            custom_fields={
                field["name"]: field.get("display_value")
                for field in task.get("custom_fields", [])
            },
            url=task.get("permalink_url"),
        )

    def _normalize_story(
        self,
        story: Dict[str, Any],
        work_item_id: str,
    ) -> NormalizedComment:
        """Normalize an Asana story (comment)."""
        return NormalizedComment(
            source_id=story["gid"],
            work_item_id=work_item_id,
            author_id=story.get("created_by", {}).get("gid", ""),
            body=story.get("text", ""),
            created_at=datetime.fromisoformat(
                story.get("created_at", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                story.get("created_at", "").replace("Z", "+00:00")
            ),  # Asana doesn't track story updates
            raw_data=story,
        )


__all__ = ["AsanaAdapter"]

