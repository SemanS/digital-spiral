"""Jira Cloud REST adapter with Basic Auth (email + API token)."""

from __future__ import annotations

import base64
import json
import time
from typing import Any

import requests

from .exceptions import (
    JiraBadRequest,
    JiraConflict,
    JiraNotFound,
    JiraRateLimited,
    JiraServerError,
    JiraUnauthorized,
)


class JiraCloudAdapter:
    """Jira Cloud adapter using Basic Auth (email + API token)."""

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        timeout: float = 10.0,
        user_agent: str = "DigitalSpiralAdapter/1.0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        
        # Jira Cloud uses Basic Auth: base64(email:api_token)
        auth_string = f"{email}:{api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        self.session.headers.update(
            {
                "Authorization": f"Basic {auth_b64}",
                "User-Agent": user_agent,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self.timeout = timeout

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.status_code < 400:
            return
        try:
            body = response.json()
        except json.JSONDecodeError:
            body = {"error": response.text}

        if response.status_code == 400:
            raise JiraBadRequest(body)
        if response.status_code == 401:
            raise JiraUnauthorized(body)
        if response.status_code == 404:
            raise JiraNotFound(body)
        if response.status_code == 409:
            raise JiraConflict(body)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            # Pass retry_after correctly; Optional message via args
            raise JiraRateLimited(
                retry_after=int(retry_after) if retry_after else None,
                *([str(body)] if body else [])
            )
        if response.status_code >= 500:
            raise JiraServerError(body)
        response.raise_for_status()

    def _call(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers: dict[str, str] = {}
        if extra_headers:
            headers.update(extra_headers)

        attempts = 0
        max_429 = 3
        max_5xx = 2
        backoff_schedule = [0.5, 1.0, 2.0]

        while True:
            response = self.session.request(
                method,
                url,
                params=params,
                json=json_body,
                headers=headers,
                timeout=self.timeout,
            )
            try:
                self._raise_for_status(response)
            except JiraRateLimited as exc:
                if attempts >= max_429 - 1:
                    raise
                sleep_seconds = (
                    exc.retry_after
                    if exc.retry_after is not None
                    else backoff_schedule[min(attempts, len(backoff_schedule) - 1)]
                )
                time.sleep(sleep_seconds)
                attempts += 1
                continue
            except JiraServerError:
                if attempts >= max_5xx - 1:
                    raise
                sleep_seconds = backoff_schedule[min(attempts, len(backoff_schedule) - 1)]
                time.sleep(sleep_seconds)
                attempts += 1
                continue

            if response.headers.get("content-type", "").startswith("application/json"):
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return {}
            return {}

    def get_myself(self) -> dict[str, Any]:
        """Get current user info."""
        return self._call("GET", "/rest/api/3/myself")

    def search(self, jql: str, max_results: int = 50, start_at: int = 0, fields: list[str] | None = None) -> dict[str, Any]:
        """Search for issues using JQL.

        Note: Some Jira instances return 410 Gone for /rest/api/3/search endpoints.
        This method tries multiple approaches:
        1. Try /rest/api/3/search (standard endpoint)
        2. If that fails with 410, try Agile API via boards
        """
        if fields is None:
            fields = ["summary", "status", "assignee", "priority", "created", "updated", "issuetype", "project"]

        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields)
        }

        if start_at > 0:
            params["startAt"] = start_at

        # Try standard search endpoint first
        try:
            return self._call(
                "GET",
                "/rest/api/3/search",
                params=params,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Search failed with: {e}")

            # If 410 Gone, try Agile API as fallback
            if "410" in str(e):
                logger.info(f"Got 410 Gone, trying Agile API fallback for JQL: {jql}")
                # Extract project key from JQL (simple parsing)
                import re
                match = re.search(r'project\s*=\s*["\']?(\w+)["\']?', jql, re.IGNORECASE)
                if match:
                    project_key = match.group(1)
                    logger.info(f"Extracted project key: {project_key}")
                    return self._search_via_agile_api(project_key, max_results, fields)
                else:
                    logger.error(f"Could not extract project key from JQL: {jql}")
            # Re-raise if not 410 or couldn't parse project
            logger.info(f"Re-raising exception")
            raise

    def _search_via_agile_api(self, project_key: str, max_results: int, fields: list[str]) -> dict[str, Any]:
        """Fallback search using Agile API when standard search returns 410 Gone."""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Using Agile API fallback for project {project_key}")

        # Get boards for project
        boards_result = self._call(
            "GET",
            "/rest/agile/1.0/board",
            params={"projectKeyOrId": project_key}
        )

        logger.info(f"Boards result type: {type(boards_result)}, is None: {boards_result is None}")

        if boards_result is None:
            logger.error("Boards result is None!")
            return {"issues": [], "total": 0}

        boards = boards_result.get("values", [])
        logger.info(f"Found {len(boards)} boards")

        if not boards:
            # Return empty result if no boards
            return {"issues": [], "total": 0}

        # Get issues from first board
        board_id = boards[0]["id"]
        logger.info(f"Getting issues from board {board_id}")

        result = self._call(
            "GET",
            f"/rest/agile/1.0/board/{board_id}/issue",
            params={
                "maxResults": max_results,
                "fields": ",".join(fields),
            }
        )

        logger.info(f"Result type: {type(result)}, is None: {result is None}")
        if result:
            logger.info(f"Issues count: {len(result.get('issues', []))}")

        return result

    def get_issue(self, issue_key: str) -> dict[str, Any]:
        """Get issue by key."""
        return self._call("GET", f"/rest/api/3/issue/{issue_key}")

    def create_issue(
        self,
        project_key: str,
        issue_type_name: str,
        summary: str,
        description: Any | None = None,
        extra_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new issue."""
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "issuetype": {"name": issue_type_name},
            "summary": summary,
        }
        
        if description:
            fields["description"] = description
        
        if extra_fields:
            fields.update(extra_fields)
        
        return self._call("POST", "/rest/api/3/issue", json_body={"fields": fields})

    def get_project(self, project_key: str) -> dict[str, Any]:
        """Get project by key."""
        return self._call("GET", f"/rest/api/3/project/{project_key}")

    def list_projects(self) -> list[dict[str, Any]]:
        """List all projects."""
        result = self._call("GET", "/rest/api/3/project")
        return result if isinstance(result, list) else []

    def add_comment(self, issue_key: str, body: Any) -> dict[str, Any]:
        """Add a comment to an issue."""
        return self._call(
            "POST",
            f"/rest/api/3/issue/{issue_key}/comment",
            json_body={"body": body},
        )

    def get_comments(self, issue_key: str) -> dict[str, Any]:
        """Get all comments for an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")

        Returns:
            Dictionary with comments list
        """
        return self._call("GET", f"/rest/api/3/issue/{issue_key}/comment")

    def delete_comment(self, issue_key: str, comment_id: str) -> None:
        """Delete a comment from an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")
            comment_id: Comment ID to delete
        """
        self._call("DELETE", f"/rest/api/3/issue/{issue_key}/comment/{comment_id}")

    def add_watcher(self, issue_key: str, account_id: str) -> None:
        """Add a watcher to an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")
            account_id: User account ID
        """
        self._call(
            "POST",
            f"/rest/api/3/issue/{issue_key}/watchers",
            json_body=account_id,
            extra_headers={"Content-Type": "application/json"}
        )

    def get_watchers(self, issue_key: str) -> dict[str, Any]:
        """Get all watchers for an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")

        Returns:
            Dictionary with watchers list
        """
        return self._call("GET", f"/rest/api/3/issue/{issue_key}/watchers")

    def remove_watcher(self, issue_key: str, account_id: str) -> None:
        """Remove a watcher from an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")
            account_id: User account ID to remove
        """
        self._call("DELETE", f"/rest/api/3/issue/{issue_key}/watchers?accountId={account_id}")

    def link_issues(self, inward_issue: str, outward_issue: str, link_type: str) -> dict[str, Any]:
        """Link two issues together.

        Args:
            inward_issue: First issue key
            outward_issue: Second issue key
            link_type: Link type (e.g., 'Blocks', 'Relates', 'Duplicates')

        Returns:
            Dictionary with link result
        """
        return self._call(
            "POST",
            "/rest/api/3/issueLink",
            json_body={
                "type": {"name": link_type},
                "inwardIssue": {"key": inward_issue},
                "outwardIssue": {"key": outward_issue}
            }
        )

    def get_issue_links(self, issue_key: str) -> list[dict[str, Any]]:
        """Get all links for an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")

        Returns:
            List of issue links
        """
        issue = self._call("GET", f"/rest/api/3/issue/{issue_key}", params={"fields": "issuelinks"})
        return issue.get("fields", {}).get("issuelinks", [])

    def search_users(self, query: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Search for users.

        Args:
            query: Search query (username, email, or display name)
            max_results: Maximum number of results

        Returns:
            List of users
        """
        result = self._call(
            "GET",
            "/rest/api/3/user/search",
            params={"query": query, "maxResults": max_results}
        )
        return result if isinstance(result, list) else []

    def update_issue_field(self, issue_key: str, field_name: str, field_value: Any) -> None:
        """Update a single field on an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")
            field_name: Field name (e.g., "priority", "labels", "description")
            field_value: New field value
        """
        self._call(
            "PUT",
            f"/rest/api/3/issue/{issue_key}",
            json_body={"fields": {field_name: field_value}}
        )

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        """Transition an issue to a new status."""
        self._call(
            "POST",
            f"/rest/api/3/issue/{issue_key}/transitions",
            json_body={"transition": {"id": transition_id}},
        )

    def get_transitions(self, issue_key: str) -> list[dict[str, Any]]:
        """Get available transitions for an issue."""
        result = self._call("GET", f"/rest/api/3/issue/{issue_key}/transitions")
        return result.get("transitions", [])

    def list_boards(self, start_at: int = 0, max_results: int = 50) -> dict[str, Any]:
        """List all boards."""
        return self._call(
            "GET",
            "/rest/agile/1.0/board",
            params={"startAt": start_at, "maxResults": max_results}
        )

    def list_sprints(self, board_id: int, start_at: int = 0, max_results: int = 50) -> dict[str, Any]:
        """List sprints for a board."""
        return self._call(
            "GET",
            f"/rest/agile/1.0/board/{board_id}/sprint",
            params={"startAt": start_at, "maxResults": max_results}
        )

    def create_sprint(self, board_id: int, name: str, start_date: str = None, end_date: str = None, goal: str = None) -> dict[str, Any]:
        """Create a new sprint."""
        payload: dict[str, Any] = {
            "originBoardId": board_id,
            "name": name
        }
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        if goal:
            payload["goal"] = goal

        return self._call("POST", "/rest/agile/1.0/sprint", json_body=payload)

    def move_issues_to_sprint(self, sprint_id: int, issue_keys: list[str]) -> None:
        """Move issues to a sprint."""
        self._call(
            "POST",
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            json_body={"issues": issue_keys}
        )

    def add_worklog(self, issue_key: str, time_spent_seconds: int, started: str, comment: str = None) -> dict[str, Any]:
        """Add worklog entry to an issue.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")
            time_spent_seconds: Time spent in seconds (e.g., 28800 = 8 hours)
            started: Start time in ISO format (e.g., "2025-01-15T09:00:00.000+0000")
            comment: Optional comment for the worklog
        """
        payload: dict[str, Any] = {
            "timeSpentSeconds": time_spent_seconds,
            "started": started
        }
        if comment:
            payload["comment"] = {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": comment
                    }]
                }]
            }

        return self._call(
            "POST",
            f"/rest/api/3/issue/{issue_key}/worklog",
            json_body=payload
        )

    def update_sprint(self, sprint_id: int, state: str = None, start_date: str = None, end_date: str = None) -> dict[str, Any]:
        """Update sprint state.

        Args:
            sprint_id: Sprint ID
            state: Sprint state ("active", "closed", "future")
            start_date: Start date in ISO format
            end_date: End date in ISO format
        """
        payload: dict[str, Any] = {}
        if state:
            payload["state"] = state
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date

        return self._call(
            "POST",
            f"/rest/agile/1.0/sprint/{sprint_id}",
            json_body=payload
        )

    def assign_issue(self, issue_key: str, account_id: str | None) -> None:
        """Assign an issue to a user.

        Args:
            issue_key: Issue key (e.g., "SCRUM-123")
            account_id: User account ID to assign to, or None to unassign
        """
        payload: dict[str, Any] = {}
        if account_id is not None:
            payload["accountId"] = account_id
        else:
            # To unassign, send null
            payload["accountId"] = None

        self._call(
            "PUT",
            f"/rest/api/3/issue/{issue_key}/assignee",
            json_body=payload
        )
