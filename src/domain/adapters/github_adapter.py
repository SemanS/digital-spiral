"""GitHub adapter implementation."""

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


class GitHubAdapter(SourceAdapter):
    """Adapter for GitHub Issues."""

    # Status mapping from GitHub to normalized
    STATUS_MAP = {
        "open": WorkItemStatus.TODO,
        "closed": WorkItemStatus.DONE,
    }

    # Priority mapping (from labels)
    PRIORITY_MAP = {
        "priority: critical": WorkItemPriority.CRITICAL,
        "priority: high": WorkItemPriority.HIGH,
        "priority: medium": WorkItemPriority.MEDIUM,
        "priority: low": WorkItemPriority.LOW,
        "p0": WorkItemPriority.CRITICAL,
        "p1": WorkItemPriority.HIGH,
        "p2": WorkItemPriority.MEDIUM,
        "p3": WorkItemPriority.LOW,
    }

    # Type mapping (from labels)
    TYPE_MAP = {
        "bug": WorkItemType.BUG,
        "enhancement": WorkItemType.FEATURE,
        "feature": WorkItemType.FEATURE,
        "task": WorkItemType.TASK,
        "story": WorkItemType.STORY,
    }

    def __init__(
        self,
        instance_id: UUID,
        base_url: str,
        auth_config: Dict[str, Any],
    ):
        """Initialize GitHub adapter.

        Args:
            instance_id: Instance UUID
            base_url: GitHub API base URL (default: https://api.github.com)
            auth_config: Dict with 'token' (personal access token or GitHub App token)
        """
        super().__init__(instance_id, base_url, auth_config)
        self.client = httpx.AsyncClient(
            base_url=base_url or "https://api.github.com",
            headers={
                "Authorization": f"token {auth_config['token']}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30.0,
        )

    async def test_connection(self) -> bool:
        """Test connection to GitHub."""
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
        """Fetch issues from GitHub.

        Args:
            project_id: Repository in format "owner/repo"
            updated_since: Only fetch items updated after this time
            limit: Maximum number of items to fetch
        """
        if not project_id:
            raise ValueError("project_id (owner/repo) is required for GitHub")
        
        params = {
            "state": "all",
            "per_page": min(limit, 100),
            "sort": "updated",
            "direction": "desc",
        }
        
        if updated_since:
            params["since"] = updated_since.isoformat()
        
        response = await self.client.get(
            f"/repos/{project_id}/issues",
            params=params,
        )
        response.raise_for_status()
        
        issues = response.json()
        # Filter out pull requests (GitHub API returns both)
        issues = [issue for issue in issues if "pull_request" not in issue]
        
        return [self._normalize_issue(issue, project_id) for issue in issues]

    async def fetch_work_item(self, work_item_id: str) -> NormalizedWorkItem:
        """Fetch a single GitHub issue.

        Args:
            work_item_id: In format "owner/repo#number"
        """
        owner, repo, number = self._parse_issue_id(work_item_id)
        
        response = await self.client.get(f"/repos/{owner}/{repo}/issues/{number}")
        response.raise_for_status()
        
        return self._normalize_issue(response.json(), f"{owner}/{repo}")

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
        """Create a new GitHub issue."""
        payload = {
            "title": title,
            "body": description or "",
        }
        
        # Add labels for type and priority
        labels = []
        if type != WorkItemType.TASK:
            labels.append(self._denormalize_type(type))
        if priority != WorkItemPriority.MEDIUM:
            labels.append(self._denormalize_priority(priority))
        
        if labels:
            payload["labels"] = labels
        
        if assignee_id:
            payload["assignees"] = [assignee_id]
        
        # Add custom labels
        if "labels" in kwargs:
            payload["labels"] = payload.get("labels", []) + kwargs["labels"]
        
        response = await self.client.post(
            f"/repos/{project_id}/issues",
            json=payload,
        )
        response.raise_for_status()
        
        return self._normalize_issue(response.json(), project_id)

    async def update_work_item(
        self,
        work_item_id: str,
        **fields,
    ) -> NormalizedWorkItem:
        """Update a GitHub issue."""
        owner, repo, number = self._parse_issue_id(work_item_id)
        
        response = await self.client.patch(
            f"/repos/{owner}/{repo}/issues/{number}",
            json=fields,
        )
        response.raise_for_status()
        
        return self._normalize_issue(response.json(), f"{owner}/{repo}")

    async def transition_work_item(
        self,
        work_item_id: str,
        to_status: WorkItemStatus,
        comment: Optional[str] = None,
    ) -> NormalizedWorkItem:
        """Transition a GitHub issue (open/close)."""
        owner, repo, number = self._parse_issue_id(work_item_id)
        
        # GitHub only has open/closed states
        state = "closed" if to_status == WorkItemStatus.DONE else "open"
        
        payload = {"state": state}
        
        response = await self.client.patch(
            f"/repos/{owner}/{repo}/issues/{number}",
            json=payload,
        )
        response.raise_for_status()
        
        # Add comment if provided
        if comment:
            await self.add_comment(work_item_id, comment)
        
        return self._normalize_issue(response.json(), f"{owner}/{repo}")

    async def add_comment(
        self,
        work_item_id: str,
        body: str,
    ) -> NormalizedComment:
        """Add a comment to a GitHub issue."""
        owner, repo, number = self._parse_issue_id(work_item_id)
        
        response = await self.client.post(
            f"/repos/{owner}/{repo}/issues/{number}/comments",
            json={"body": body},
        )
        response.raise_for_status()
        
        return self._normalize_comment(response.json(), work_item_id)

    async def fetch_comments(
        self,
        work_item_id: str,
    ) -> List[NormalizedComment]:
        """Fetch comments for a GitHub issue."""
        owner, repo, number = self._parse_issue_id(work_item_id)
        
        response = await self.client.get(
            f"/repos/{owner}/{repo}/issues/{number}/comments"
        )
        response.raise_for_status()
        
        return [
            self._normalize_comment(comment, work_item_id)
            for comment in response.json()
        ]

    async def fetch_transitions(
        self,
        work_item_id: str,
    ) -> List[NormalizedTransition]:
        """Fetch transitions for a GitHub issue.

        GitHub doesn't have a direct transition history, so we parse
        the timeline events.
        """
        owner, repo, number = self._parse_issue_id(work_item_id)
        
        response = await self.client.get(
            f"/repos/{owner}/{repo}/issues/{number}/timeline",
            headers={"Accept": "application/vnd.github.mockingbird-preview+json"},
        )
        response.raise_for_status()
        
        transitions = []
        for event in response.json():
            if event.get("event") in ["closed", "reopened"]:
                transitions.append(
                    NormalizedTransition(
                        work_item_id=work_item_id,
                        from_status=WorkItemStatus.TODO if event["event"] == "closed" else WorkItemStatus.DONE,
                        to_status=WorkItemStatus.DONE if event["event"] == "closed" else WorkItemStatus.TODO,
                        actor_id=event.get("actor", {}).get("login", ""),
                        timestamp=datetime.fromisoformat(
                            event.get("created_at", "").replace("Z", "+00:00")
                        ),
                        raw_data=event,
                    )
                )
        
        return transitions

    def normalize_status(self, source_status: str) -> WorkItemStatus:
        """Normalize GitHub status."""
        return self.STATUS_MAP.get(source_status.lower(), WorkItemStatus.TODO)

    def normalize_priority(self, source_priority: str) -> WorkItemPriority:
        """Normalize GitHub priority (from labels)."""
        return self.PRIORITY_MAP.get(source_priority.lower(), WorkItemPriority.MEDIUM)

    def normalize_type(self, source_type: str) -> WorkItemType:
        """Normalize GitHub type (from labels)."""
        return self.TYPE_MAP.get(source_type.lower(), WorkItemType.TASK)

    def _denormalize_priority(self, priority: WorkItemPriority) -> str:
        """Convert normalized priority to GitHub label."""
        priority_labels = {
            WorkItemPriority.CRITICAL: "priority: critical",
            WorkItemPriority.HIGH: "priority: high",
            WorkItemPriority.MEDIUM: "priority: medium",
            WorkItemPriority.LOW: "priority: low",
        }
        return priority_labels.get(priority, "priority: medium")

    def _denormalize_type(self, type: WorkItemType) -> str:
        """Convert normalized type to GitHub label."""
        type_labels = {
            WorkItemType.BUG: "bug",
            WorkItemType.FEATURE: "enhancement",
            WorkItemType.STORY: "story",
            WorkItemType.TASK: "task",
        }
        return type_labels.get(type, "task")

    def _parse_issue_id(self, work_item_id: str) -> tuple:
        """Parse issue ID in format 'owner/repo#number'."""
        if "#" in work_item_id:
            repo_part, number = work_item_id.split("#")
            owner, repo = repo_part.split("/")
            return owner, repo, number
        else:
            raise ValueError(f"Invalid GitHub issue ID format: {work_item_id}")

    def _normalize_issue(
        self,
        issue: Dict[str, Any],
        project_id: str,
    ) -> NormalizedWorkItem:
        """Normalize a GitHub issue to standard format."""
        # Extract priority and type from labels
        labels = [label["name"].lower() for label in issue.get("labels", [])]
        
        priority = WorkItemPriority.MEDIUM
        for label in labels:
            if label in self.PRIORITY_MAP:
                priority = self.PRIORITY_MAP[label]
                break
        
        type = WorkItemType.TASK
        for label in labels:
            if label in self.TYPE_MAP:
                type = self.TYPE_MAP[label]
                break
        
        return NormalizedWorkItem(
            source_id=str(issue["id"]),
            source_key=f"{project_id}#{issue['number']}",
            source_type=SourceType.GITHUB,
            instance_id=self.instance_id,
            title=issue["title"],
            description=issue.get("body"),
            status=self.normalize_status(issue["state"]),
            priority=priority,
            type=type,
            parent_id=None,  # GitHub doesn't have parent issues
            project_id=project_id,
            assignee_id=issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
            reporter_id=issue.get("user", {}).get("login"),
            created_at=datetime.fromisoformat(
                issue["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                issue["updated_at"].replace("Z", "+00:00")
            ),
            closed_at=datetime.fromisoformat(
                issue["closed_at"].replace("Z", "+00:00")
            ) if issue.get("closed_at") else None,
            raw_data=issue,
            custom_fields={"labels": labels},
            url=issue["html_url"],
        )

    def _normalize_comment(
        self,
        comment: Dict[str, Any],
        work_item_id: str,
    ) -> NormalizedComment:
        """Normalize a GitHub comment."""
        return NormalizedComment(
            source_id=str(comment["id"]),
            work_item_id=work_item_id,
            author_id=comment.get("user", {}).get("login", ""),
            body=comment.get("body", ""),
            created_at=datetime.fromisoformat(
                comment["created_at"].replace("Z", "+00:00")
            ),
            updated_at=datetime.fromisoformat(
                comment["updated_at"].replace("Z", "+00:00")
            ),
            raw_data=comment,
        )


__all__ = ["GitHubAdapter"]

