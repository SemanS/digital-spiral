"""Linear adapter implementation."""

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


class LinearAdapter(SourceAdapter):
    """Adapter for Linear (GraphQL API)."""

    # Status mapping from Linear to normalized
    STATUS_MAP = {
        "backlog": WorkItemStatus.TODO,
        "unstarted": WorkItemStatus.TODO,
        "started": WorkItemStatus.IN_PROGRESS,
        "in progress": WorkItemStatus.IN_PROGRESS,
        "blocked": WorkItemStatus.BLOCKED,
        "in review": WorkItemStatus.IN_REVIEW,
        "done": WorkItemStatus.DONE,
        "completed": WorkItemStatus.DONE,
        "canceled": WorkItemStatus.CANCELLED,
        "cancelled": WorkItemStatus.CANCELLED,
    }

    # Priority mapping
    PRIORITY_MAP = {
        "urgent": WorkItemPriority.CRITICAL,
        "high": WorkItemPriority.HIGH,
        "medium": WorkItemPriority.MEDIUM,
        "normal": WorkItemPriority.MEDIUM,
        "low": WorkItemPriority.LOW,
        "no priority": WorkItemPriority.NONE,
    }

    # Type mapping (Linear uses labels)
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
        """Initialize Linear adapter.

        Args:
            instance_id: Instance UUID
            base_url: Linear API base URL (default: https://api.linear.app/graphql)
            auth_config: Dict with 'api_key' (Linear API key)
        """
        super().__init__(instance_id, base_url, auth_config)
        self.client = httpx.AsyncClient(
            base_url=base_url or "https://api.linear.app/graphql",
            headers={
                "Authorization": auth_config['api_key'],
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def test_connection(self) -> bool:
        """Test connection to Linear."""
        query = """
        query {
            viewer {
                id
                name
            }
        }
        """
        try:
            response = await self.client.post("", json={"query": query})
            data = response.json()
            return "data" in data and "viewer" in data["data"]
        except Exception:
            return False

    async def fetch_work_items(
        self,
        project_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[NormalizedWorkItem]:
        """Fetch issues from Linear.

        Args:
            project_id: Linear project ID or team ID
            updated_since: Only fetch items updated after this time
            limit: Maximum number of items to fetch
        """
        # Build GraphQL query
        filter_parts = []
        if project_id:
            filter_parts.append(f'project: {{id: {{eq: "{project_id}"}}}}')
        if updated_since:
            filter_parts.append(f'updatedAt: {{gt: "{updated_since.isoformat()}"}}')
        
        filter_str = ", ".join(filter_parts) if filter_parts else ""
        
        query = f"""
        query {{
            issues(first: {limit}, filter: {{{filter_str}}}) {{
                nodes {{
                    id
                    identifier
                    title
                    description
                    priority
                    state {{
                        name
                        type
                    }}
                    assignee {{
                        id
                        name
                    }}
                    creator {{
                        id
                        name
                    }}
                    project {{
                        id
                        name
                    }}
                    parent {{
                        id
                    }}
                    createdAt
                    updatedAt
                    completedAt
                    url
                    labels {{
                        nodes {{
                            name
                        }}
                    }}
                }}
            }}
        }}
        """
        
        response = await self.client.post("", json={"query": query})
        response.raise_for_status()
        
        data = response.json()
        issues = data.get("data", {}).get("issues", {}).get("nodes", [])
        
        return [self._normalize_issue(issue) for issue in issues]

    async def fetch_work_item(self, work_item_id: str) -> NormalizedWorkItem:
        """Fetch a single Linear issue.

        Args:
            work_item_id: Linear issue ID or identifier (e.g., "PROJ-123")
        """
        query = f"""
        query {{
            issue(id: "{work_item_id}") {{
                id
                identifier
                title
                description
                priority
                state {{
                    name
                    type
                }}
                assignee {{
                    id
                    name
                }}
                creator {{
                    id
                    name
                }}
                project {{
                    id
                    name
                }}
                parent {{
                    id
                }}
                createdAt
                updatedAt
                completedAt
                url
                labels {{
                    nodes {{
                        name
                    }}
                }}
            }}
        }}
        """
        
        response = await self.client.post("", json={"query": query})
        response.raise_for_status()
        
        data = response.json()
        issue = data.get("data", {}).get("issue")
        
        if not issue:
            raise ValueError(f"Issue not found: {work_item_id}")
        
        return self._normalize_issue(issue)

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
        """Create a new Linear issue."""
        # Map priority to Linear priority (0-4)
        linear_priority = self._denormalize_priority(priority)
        
        mutation = f"""
        mutation {{
            issueCreate(input: {{
                title: "{title}"
                description: "{description or ''}"
                projectId: "{project_id}"
                priority: {linear_priority}
                {f'assigneeId: "{assignee_id}"' if assignee_id else ''}
            }}) {{
                success
                issue {{
                    id
                    identifier
                }}
            }}
        }}
        """
        
        response = await self.client.post("", json={"query": mutation})
        response.raise_for_status()
        
        data = response.json()
        created = data.get("data", {}).get("issueCreate", {})
        
        if not created.get("success"):
            raise ValueError("Failed to create issue")
        
        issue_id = created.get("issue", {}).get("id")
        return await self.fetch_work_item(issue_id)

    async def update_work_item(
        self,
        work_item_id: str,
        **fields,
    ) -> NormalizedWorkItem:
        """Update a Linear issue."""
        # Build update fields
        update_fields = []
        for key, value in fields.items():
            if isinstance(value, str):
                update_fields.append(f'{key}: "{value}"')
            else:
                update_fields.append(f'{key}: {value}')
        
        mutation = f"""
        mutation {{
            issueUpdate(
                id: "{work_item_id}"
                input: {{{", ".join(update_fields)}}}
            ) {{
                success
                issue {{
                    id
                }}
            }}
        }}
        """
        
        response = await self.client.post("", json={"query": mutation})
        response.raise_for_status()
        
        return await self.fetch_work_item(work_item_id)

    async def transition_work_item(
        self,
        work_item_id: str,
        to_status: WorkItemStatus,
        comment: Optional[str] = None,
    ) -> NormalizedWorkItem:
        """Transition a Linear issue.

        Note: Linear uses state IDs, so this is simplified.
        In production, you'd need to fetch available states first.
        """
        # For simplicity, we'll just mark as completed or not
        if to_status == WorkItemStatus.DONE:
            mutation = f"""
            mutation {{
                issueUpdate(
                    id: "{work_item_id}"
                    input: {{stateId: "completed"}}
                ) {{
                    success
                }}
            }}
            """
        else:
            mutation = f"""
            mutation {{
                issueUpdate(
                    id: "{work_item_id}"
                    input: {{stateId: "in_progress"}}
                ) {{
                    success
                }}
            }}
            """
        
        response = await self.client.post("", json={"query": mutation})
        response.raise_for_status()
        
        if comment:
            await self.add_comment(work_item_id, comment)
        
        return await self.fetch_work_item(work_item_id)

    async def add_comment(
        self,
        work_item_id: str,
        body: str,
    ) -> NormalizedComment:
        """Add a comment to a Linear issue."""
        mutation = f"""
        mutation {{
            commentCreate(input: {{
                issueId: "{work_item_id}"
                body: "{body}"
            }}) {{
                success
                comment {{
                    id
                    body
                    createdAt
                    user {{
                        id
                    }}
                }}
            }}
        }}
        """
        
        response = await self.client.post("", json={"query": mutation})
        response.raise_for_status()
        
        data = response.json()
        comment = data.get("data", {}).get("commentCreate", {}).get("comment")
        
        return NormalizedComment(
            source_id=comment["id"],
            work_item_id=work_item_id,
            author_id=comment.get("user", {}).get("id", ""),
            body=comment.get("body", ""),
            created_at=datetime.fromisoformat(comment["createdAt"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(comment["createdAt"].replace("Z", "+00:00")),
            raw_data=comment,
        )

    async def fetch_comments(
        self,
        work_item_id: str,
    ) -> List[NormalizedComment]:
        """Fetch comments for a Linear issue."""
        query = f"""
        query {{
            issue(id: "{work_item_id}") {{
                comments {{
                    nodes {{
                        id
                        body
                        createdAt
                        user {{
                            id
                        }}
                    }}
                }}
            }}
        }}
        """
        
        response = await self.client.post("", json={"query": query})
        response.raise_for_status()
        
        data = response.json()
        comments = data.get("data", {}).get("issue", {}).get("comments", {}).get("nodes", [])
        
        return [
            NormalizedComment(
                source_id=comment["id"],
                work_item_id=work_item_id,
                author_id=comment.get("user", {}).get("id", ""),
                body=comment.get("body", ""),
                created_at=datetime.fromisoformat(comment["createdAt"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(comment["createdAt"].replace("Z", "+00:00")),
                raw_data=comment,
            )
            for comment in comments
        ]

    async def fetch_transitions(
        self,
        work_item_id: str,
    ) -> List[NormalizedTransition]:
        """Fetch transitions for a Linear issue."""
        # Linear doesn't expose history via GraphQL easily
        # This would require webhook integration or activity log parsing
        return []

    def normalize_status(self, source_status: str) -> WorkItemStatus:
        """Normalize Linear status."""
        return self.STATUS_MAP.get(source_status.lower(), WorkItemStatus.TODO)

    def normalize_priority(self, source_priority: str) -> WorkItemPriority:
        """Normalize Linear priority."""
        return self.PRIORITY_MAP.get(source_priority.lower(), WorkItemPriority.MEDIUM)

    def normalize_type(self, source_type: str) -> WorkItemType:
        """Normalize Linear type."""
        return self.TYPE_MAP.get(source_type.lower(), WorkItemType.TASK)

    def _denormalize_priority(self, priority: WorkItemPriority) -> int:
        """Convert normalized priority to Linear priority (0-4)."""
        priority_map = {
            WorkItemPriority.NONE: 0,
            WorkItemPriority.LOW: 1,
            WorkItemPriority.MEDIUM: 2,
            WorkItemPriority.HIGH: 3,
            WorkItemPriority.CRITICAL: 4,
        }
        return priority_map.get(priority, 2)

    def _normalize_issue(self, issue: Dict[str, Any]) -> NormalizedWorkItem:
        """Normalize a Linear issue to standard format."""
        # Extract labels
        labels = [label["name"].lower() for label in issue.get("labels", {}).get("nodes", [])]
        
        # Determine type from labels
        type = WorkItemType.TASK
        for label in labels:
            if label in self.TYPE_MAP:
                type = self.TYPE_MAP[label]
                break
        
        # Map priority (Linear uses 0-4)
        priority_value = issue.get("priority", 2)
        priority_map = {
            0: WorkItemPriority.NONE,
            1: WorkItemPriority.LOW,
            2: WorkItemPriority.MEDIUM,
            3: WorkItemPriority.HIGH,
            4: WorkItemPriority.CRITICAL,
        }
        priority = priority_map.get(priority_value, WorkItemPriority.MEDIUM)
        
        return NormalizedWorkItem(
            source_id=issue["id"],
            source_key=issue.get("identifier", issue["id"]),
            source_type=SourceType.LINEAR,
            instance_id=self.instance_id,
            title=issue.get("title", ""),
            description=issue.get("description"),
            status=self.normalize_status(issue.get("state", {}).get("name", "")),
            priority=priority,
            type=type,
            parent_id=issue.get("parent", {}).get("id") if issue.get("parent") else None,
            project_id=issue.get("project", {}).get("id"),
            assignee_id=issue.get("assignee", {}).get("id") if issue.get("assignee") else None,
            reporter_id=issue.get("creator", {}).get("id"),
            created_at=datetime.fromisoformat(issue["createdAt"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(issue["updatedAt"].replace("Z", "+00:00")),
            closed_at=datetime.fromisoformat(issue["completedAt"].replace("Z", "+00:00")) if issue.get("completedAt") else None,
            raw_data=issue,
            custom_fields={"labels": labels},
            url=issue.get("url"),
        )


__all__ = ["LinearAdapter"]

