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

        Note: Jira Cloud now requires using /rest/api/3/search/jql endpoint.
        This method uses the new endpoint with proper field expansion.
        """
        if fields is None:
            fields = ["summary", "status", "assignee", "priority", "created", "updated", "issuetype", "project"]

        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ",".join(fields)
        }

        if start_at > 0:
            # For pagination, we need to use nextPageToken from previous response
            params["startAt"] = start_at

        return self._call(
            "GET",
            "/rest/api/3/search/jql",
            params=params,
        )

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
