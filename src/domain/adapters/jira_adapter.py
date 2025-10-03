"""Jira adapter implementation."""

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


class JiraAdapter(SourceAdapter):
    """Adapter for Atlassian Jira."""

    # Status mapping from Jira to normalized
    STATUS_MAP = {
        "to do": WorkItemStatus.TODO,
        "open": WorkItemStatus.TODO,
        "backlog": WorkItemStatus.TODO,
        "in progress": WorkItemStatus.IN_PROGRESS,
        "in development": WorkItemStatus.IN_PROGRESS,
        "blocked": WorkItemStatus.BLOCKED,
        "impediment": WorkItemStatus.BLOCKED,
        "in review": WorkItemStatus.IN_REVIEW,
        "code review": WorkItemStatus.IN_REVIEW,
        "done": WorkItemStatus.DONE,
        "closed": WorkItemStatus.DONE,
        "resolved": WorkItemStatus.DONE,
        "cancelled": WorkItemStatus.CANCELLED,
        "rejected": WorkItemStatus.CANCELLED,
    }

    # Priority mapping
    PRIORITY_MAP = {
        "highest": WorkItemPriority.CRITICAL,
        "critical": WorkItemPriority.CRITICAL,
        "high": WorkItemPriority.HIGH,
        "medium": WorkItemPriority.MEDIUM,
        "low": WorkItemPriority.LOW,
        "lowest": WorkItemPriority.LOW,
    }

    # Type mapping
    TYPE_MAP = {
        "epic": WorkItemType.EPIC,
        "story": WorkItemType.STORY,
        "task": WorkItemType.TASK,
        "bug": WorkItemType.BUG,
        "sub-task": WorkItemType.SUBTASK,
        "subtask": WorkItemType.SUBTASK,
        "feature": WorkItemType.FEATURE,
    }

    def __init__(
        self,
        instance_id: UUID,
        base_url: str,
        auth_config: Dict[str, Any],
    ):
        """Initialize Jira adapter.

        Args:
            instance_id: Instance UUID
            base_url: Jira base URL (e.g., https://company.atlassian.net)
            auth_config: Dict with 'email' and 'api_token' or 'access_token'
        """
        super().__init__(instance_id, base_url, auth_config)
        self.client = httpx.AsyncClient(
            base_url=f"{base_url}/rest/api/3",
            headers=self._get_auth_headers(),
            timeout=30.0,
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if "access_token" in self.auth_config:
            return {"Authorization": f"Bearer {self.auth_config['access_token']}"}
        elif "email" in self.auth_config and "api_token" in self.auth_config:
            import base64
            credentials = f"{self.auth_config['email']}:{self.auth_config['api_token']}"
            encoded = base64.b64encode(credentials.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        else:
            raise ValueError("Invalid auth_config: need 'access_token' or 'email'+'api_token'")

    async def test_connection(self) -> bool:
        """Test connection to Jira."""
        try:
            response = await self.client.get("/myself")
            return response.status_code == 200
        except Exception:
            return False

    async def fetch_work_items(
        self,
        project_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[NormalizedWorkItem]:
        """Fetch work items from Jira."""
        jql_parts = []
        
        if project_id:
            jql_parts.append(f"project = {project_id}")
        
        if updated_since:
            jql_parts.append(f"updated >= '{updated_since.strftime('%Y-%m-%d %H:%M')}'")
        
        jql = " AND ".join(jql_parts) if jql_parts else "order by updated DESC"
        
        response = await self.client.get(
            "/search",
            params={
                "jql": jql,
                "maxResults": limit,
                "fields": "summary,description,status,priority,issuetype,parent,project,assignee,reporter,created,updated,resolutiondate",
            },
        )
        response.raise_for_status()
        
        data = response.json()
        return [self._normalize_issue(issue) for issue in data.get("issues", [])]

    async def fetch_work_item(self, work_item_id: str) -> NormalizedWorkItem:
        """Fetch a single work item."""
        response = await self.client.get(f"/issue/{work_item_id}")
        response.raise_for_status()
        return self._normalize_issue(response.json())

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
        """Create a new Jira issue."""
        # Map normalized type to Jira type
        jira_type = self._denormalize_type(type)
        jira_priority = self._denormalize_priority(priority)
        
        payload = {
            "fields": {
                "project": {"key": project_id},
                "summary": title,
                "issuetype": {"name": jira_type},
                "priority": {"name": jira_priority},
            }
        }
        
        if description:
            payload["fields"]["description"] = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            }
        
        if assignee_id:
            payload["fields"]["assignee"] = {"id": assignee_id}
        
        # Add custom fields
        payload["fields"].update(kwargs)
        
        response = await self.client.post("/issue", json=payload)
        response.raise_for_status()
        
        created = response.json()
        return await self.fetch_work_item(created["key"])

    async def update_work_item(
        self,
        work_item_id: str,
        **fields,
    ) -> NormalizedWorkItem:
        """Update a Jira issue."""
        payload = {"fields": fields}
        
        response = await self.client.put(f"/issue/{work_item_id}", json=payload)
        response.raise_for_status()
        
        return await self.fetch_work_item(work_item_id)

    async def transition_work_item(
        self,
        work_item_id: str,
        to_status: WorkItemStatus,
        comment: Optional[str] = None,
    ) -> NormalizedWorkItem:
        """Transition a Jira issue."""
        # Get available transitions
        response = await self.client.get(f"/issue/{work_item_id}/transitions")
        response.raise_for_status()
        transitions = response.json()["transitions"]
        
        # Find matching transition
        target_status = self._denormalize_status(to_status)
        transition_id = None
        for t in transitions:
            if t["to"]["name"].lower() == target_status.lower():
                transition_id = t["id"]
                break
        
        if not transition_id:
            raise ValueError(f"No transition found to status: {target_status}")
        
        # Perform transition
        payload = {"transition": {"id": transition_id}}
        if comment:
            payload["update"] = {
                "comment": [{"add": {"body": comment}}]
            }
        
        response = await self.client.post(
            f"/issue/{work_item_id}/transitions",
            json=payload,
        )
        response.raise_for_status()
        
        return await self.fetch_work_item(work_item_id)

    async def add_comment(
        self,
        work_item_id: str,
        body: str,
    ) -> NormalizedComment:
        """Add a comment to a Jira issue."""
        payload = {"body": body}
        
        response = await self.client.post(
            f"/issue/{work_item_id}/comment",
            json=payload,
        )
        response.raise_for_status()
        
        comment_data = response.json()
        return self._normalize_comment(comment_data, work_item_id)

    async def fetch_comments(
        self,
        work_item_id: str,
    ) -> List[NormalizedComment]:
        """Fetch comments for a Jira issue."""
        response = await self.client.get(f"/issue/{work_item_id}/comment")
        response.raise_for_status()
        
        data = response.json()
        return [
            self._normalize_comment(comment, work_item_id)
            for comment in data.get("comments", [])
        ]

    async def fetch_transitions(
        self,
        work_item_id: str,
    ) -> List[NormalizedTransition]:
        """Fetch transitions for a Jira issue."""
        response = await self.client.get(
            f"/issue/{work_item_id}",
            params={"expand": "changelog"},
        )
        response.raise_for_status()
        
        data = response.json()
        transitions = []
        
        for history in data.get("changelog", {}).get("histories", []):
            for item in history.get("items", []):
                if item.get("field") == "status":
                    transitions.append(
                        NormalizedTransition(
                            work_item_id=work_item_id,
                            from_status=self.normalize_status(item.get("fromString", "")),
                            to_status=self.normalize_status(item.get("toString", "")),
                            actor_id=history.get("author", {}).get("accountId", ""),
                            timestamp=datetime.fromisoformat(
                                history.get("created", "").replace("Z", "+00:00")
                            ),
                            raw_data=history,
                        )
                    )
        
        return transitions

    def normalize_status(self, source_status: str) -> WorkItemStatus:
        """Normalize Jira status."""
        return self.STATUS_MAP.get(source_status.lower(), WorkItemStatus.TODO)

    def normalize_priority(self, source_priority: str) -> WorkItemPriority:
        """Normalize Jira priority."""
        return self.PRIORITY_MAP.get(source_priority.lower(), WorkItemPriority.MEDIUM)

    def normalize_type(self, source_type: str) -> WorkItemType:
        """Normalize Jira issue type."""
        return self.TYPE_MAP.get(source_type.lower(), WorkItemType.TASK)

    def _denormalize_status(self, status: WorkItemStatus) -> str:
        """Convert normalized status back to Jira status."""
        reverse_map = {v: k for k, v in self.STATUS_MAP.items()}
        return reverse_map.get(status, "To Do").title()

    def _denormalize_priority(self, priority: WorkItemPriority) -> str:
        """Convert normalized priority back to Jira priority."""
        reverse_map = {v: k for k, v in self.PRIORITY_MAP.items()}
        return reverse_map.get(priority, "Medium").title()

    def _denormalize_type(self, type: WorkItemType) -> str:
        """Convert normalized type back to Jira type."""
        reverse_map = {v: k for k, v in self.TYPE_MAP.items()}
        return reverse_map.get(type, "Task").title()

    def _normalize_issue(self, issue: Dict[str, Any]) -> NormalizedWorkItem:
        """Normalize a Jira issue to standard format."""
        fields = issue.get("fields", {})
        
        return NormalizedWorkItem(
            source_id=issue["id"],
            source_key=issue["key"],
            source_type=SourceType.JIRA,
            instance_id=self.instance_id,
            title=fields.get("summary", ""),
            description=self._extract_description(fields.get("description")),
            status=self.normalize_status(fields.get("status", {}).get("name", "")),
            priority=self.normalize_priority(fields.get("priority", {}).get("name", "")),
            type=self.normalize_type(fields.get("issuetype", {}).get("name", "")),
            parent_id=fields.get("parent", {}).get("key"),
            project_id=fields.get("project", {}).get("key"),
            assignee_id=fields.get("assignee", {}).get("accountId"),
            reporter_id=fields.get("reporter", {}).get("accountId"),
            created_at=datetime.fromisoformat(
                fields.get("created", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                fields.get("updated", "").replace("Z", "+00:00")
            ),
            closed_at=datetime.fromisoformat(
                fields.get("resolutiondate", "").replace("Z", "+00:00")
            ) if fields.get("resolutiondate") else None,
            raw_data=issue,
            custom_fields={},
            url=f"{self.base_url}/browse/{issue['key']}",
        )

    def _normalize_comment(
        self,
        comment: Dict[str, Any],
        work_item_id: str,
    ) -> NormalizedComment:
        """Normalize a Jira comment."""
        return NormalizedComment(
            source_id=comment["id"],
            work_item_id=work_item_id,
            author_id=comment.get("author", {}).get("accountId", ""),
            body=comment.get("body", ""),
            created_at=datetime.fromisoformat(
                comment.get("created", "").replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                comment.get("updated", "").replace("Z", "+00:00")
            ),
            raw_data=comment,
        )

    def _extract_description(self, description: Any) -> Optional[str]:
        """Extract plain text from Jira ADF description."""
        if not description:
            return None
        
        if isinstance(description, str):
            return description
        
        # Extract text from ADF format
        if isinstance(description, dict):
            content = description.get("content", [])
            text_parts = []
            for block in content:
                if block.get("type") == "paragraph":
                    for item in block.get("content", []):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
            return " ".join(text_parts)
        
        return None


__all__ = ["JiraAdapter"]

