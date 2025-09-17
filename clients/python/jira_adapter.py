"""Synchronous Jira REST adapter with retry and rich error handling."""

from __future__ import annotations

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


class JiraAdapter:
    """Thin wrapper around Jira REST endpoints with opinionated defaults."""

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 10.0,
        user_agent: str = "MockJiraAdapter/1.0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "User-Agent": user_agent,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _raise_for_status(self, resp: requests.Response) -> None:
        content_type = resp.headers.get("content-type", "")
        body: dict[str, Any] = {}
        if content_type.startswith("application/json"):
            try:
                body = resp.json()
            except Exception:
                body = {}
        message_source: list[str] | None = None
        if isinstance(body, dict):
            if isinstance(body.get("errorMessages"), list):
                message_source = body["errorMessages"]
        if not message_source:
            text = resp.text or resp.reason
            message_source = [text or "Unknown error"]
        message = message_source[0]

        status = resp.status_code
        if status == 400:
            raise JiraBadRequest(message)
        if status in (401, 403):
            raise JiraUnauthorized(message)
        if status == 404:
            raise JiraNotFound(message)
        if status == 409:
            raise JiraConflict(message)
        if status == 429:
            retry_after_header = resp.headers.get("Retry-After")
            retry_after: float | None
            if retry_after_header is not None:
                try:
                    retry_after = float(retry_after_header)
                except ValueError:
                    retry_after = None
            else:
                retry_after = None
            raise JiraRateLimited(retry_after, message)
        if 500 <= status < 600:
            raise JiraServerError(message)
        resp.raise_for_status()

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

    # ------------------------------------------------------------------
    # Platform endpoints
    # ------------------------------------------------------------------
    def create_issue(
        self,
        project_key: str,
        issue_type_id: str,
        summary: str,
        description_adf: dict[str, Any] | None = None,
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload_fields: dict[str, Any] = {
            "project": {"key": project_key},
            "issuetype": {"id": issue_type_id},
            "summary": summary,
        }
        if description_adf:
            payload_fields["description"] = description_adf
        if fields:
            payload_fields.update(fields)
        return self._call(
            "POST",
            "/rest/api/3/issue",
            json_body={"fields": payload_fields},
        )

    def get_issue(self, key: str) -> dict[str, Any]:
        return self._call("GET", f"/rest/api/3/issue/{key}")

    def list_transitions(self, key: str) -> list[dict[str, Any]]:
        response = self._call("GET", f"/rest/api/3/issue/{key}/transitions")
        transitions = response.get("transitions", [])
        if not isinstance(transitions, list):
            return []
        return transitions

    def transition_issue(self, key: str, transition_id: str) -> dict[str, Any]:
        return self._call(
            "POST",
            f"/rest/api/3/issue/{key}/transitions",
            json_body={"transition": {"id": transition_id}},
        )

    def add_comment(self, key: str, body_adf: dict[str, Any]) -> dict[str, Any]:
        return self._call(
            "POST",
            f"/rest/api/3/issue/{key}/comment",
            json_body={"body": body_adf},
        )

    def search(self, jql: str, start_at: int = 0, max_results: int = 50) -> dict[str, Any]:
        try:
            return self._call(
                "POST",
                "/rest/api/3/search",
                json_body={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": max_results,
                },
            )
        except JiraNotFound:
            return self._call(
                "GET",
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": max_results,
                },
            )

    def list_boards(self, start_at: int = 0, max_results: int = 50) -> dict[str, Any]:
        return self._call(
            "GET",
            "/rest/agile/1.0/board",
            params={"startAt": start_at, "maxResults": max_results},
        )

    def list_sprints(
        self,
        board_id: int,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict[str, Any]:
        return self._call(
            "GET",
            f"/rest/agile/1.0/board/{board_id}/sprint",
            params={"startAt": start_at, "maxResults": max_results},
        )

    def create_request(
        self,
        service_desk_id: str,
        request_type_id: str,
        summary: str,
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_fields = [
            {"fieldId": "summary", "value": summary},
        ]
        if fields:
            for key, value in fields.items():
                request_fields.append({"fieldId": key, "value": value})
        payload = {
            "serviceDeskId": service_desk_id,
            "requestTypeId": request_type_id,
            "requestFieldValues": request_fields,
        }
        return self._call(
            "POST",
            "/rest/servicedeskapi/request",
            json_body=payload,
        )

    def get_request(self, request_id: str) -> dict[str, Any]:
        return self._call(
            "GET",
            f"/rest/servicedeskapi/request/{request_id}",
        )

    def register_webhook(
        self,
        url: str,
        jql: str,
        events: list[str] | None = None,
        secret: str | None = None,
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {"url": url, "jqlFilter": jql}
        if events:
            body["events"] = events
        if secret:
            body["secret"] = secret
        response = self._call(
            "POST",
            "/rest/api/3/webhook",
            json_body={"webhooks": [body]},
        )
        return response.get("webhookRegistrationResult", [])
