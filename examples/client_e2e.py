"""End-to-end client script for the Digital Spiral mock Jira server.

This script demonstrates the canonical client workflow expected from the app:
- optional webhook registration (if MOCKJIRA_WEBHOOK_URL is set)
- create a Jira issue
- list transitions and perform a transition
- add a comment (ADF)
- search for the created issue
- create a Service Management (JSM) request
- list Agile sprints for a board

It reads configuration from environment variables:
- JIRA_BASE_URL (default: http://localhost:9000)
- JIRA_TOKEN (default: mock-token)
- MOCKJIRA_WEBHOOK_URL (optional)
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

from clients.python.jira_adapter import JiraAdapter
import requests


def _adapter() -> JiraAdapter:
    return JiraAdapter(
        os.getenv("JIRA_BASE_URL", "http://localhost:9000"),
        os.getenv("JIRA_TOKEN", "mock-token"),
    )


def _list_project_keys(adapter: JiraAdapter) -> list[str]:
    try:
        resp = adapter.session.get(
            f"{adapter.base_url}/rest/api/3/project", timeout=adapter.timeout
        )
        resp.raise_for_status()
        data = resp.json()
        values = data.get("values", []) if isinstance(data, dict) else []
        keys: list[str] = []
        if isinstance(values, list):
            for item in values:
                key = item.get("key") if isinstance(item, dict) else None
                if isinstance(key, str) and key:
                    keys.append(key)
        return keys
    except Exception:
        return []


def _pick_project_key(adapter: JiraAdapter) -> str:
    keys = _list_project_keys(adapter)
    return keys[0] if keys else "DEV"


def main() -> Dict[str, Any]:
    adapter = _adapter()

    # Discover a valid project key from the server seed
    project_key = _pick_project_key(adapter)

    # 1) Optional: register webhook for demo purposes
    webhook_url = os.getenv("MOCKJIRA_WEBHOOK_URL")
    webhook_reg: list[dict[str, Any]] | None = None
    if webhook_url:
        webhook_reg = adapter.register_webhook(
            webhook_url,
            f"project = {project_key}",
            events=["jira:issue_created"],
        )

    started = datetime.utcnow().isoformat()

    # 2) Create issue (Platform API)
    issue = adapter.create_issue(
        project_key=project_key,
        issue_type_id="10001",
        summary="Client E2E demo",
        description_adf={
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Created by client_e2e script"}
                    ],
                }
            ],
        },
    )
    key = issue["key"]

    # 3) List transitions and perform one
    transitions = adapter.list_transitions(key)
    chosen_transition: str | None = transitions[0]["id"] if transitions else None
    transition_result: dict[str, Any] | None = None
    if chosen_transition:
        transition_result = adapter.transition_issue(key, chosen_transition)

    # 4) Add comment (ADF)
    comment = adapter.add_comment(
        key,
        {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Draft reply: working on it."}
                    ],
                }
            ],
        },
    )

    # 5) Search for the created issue (tolerate server variations)
    search: dict[str, Any] | None = None
    search_error: str | None = None
    try:
        search = adapter.search(f'key = "{key}"')
    except Exception as exc:
        search_error = str(exc)

    # 6) Create a JSM request (Service Management) if SUP exists in projects
    jsm_request: dict[str, Any] | None = None
    project_keys = _list_project_keys(adapter)
    if "SUP" in project_keys:
        jsm_request = adapter.create_request(
            service_desk_id="1",
            request_type_id="100",
            summary="Laptop request from client_e2e",
            fields={"description": "Need a new laptop for development"},
        )

    # 7) List Agile sprints for a board (discover first board)
    boards = adapter.list_boards()
    board_values = boards.get("values", []) if isinstance(boards, dict) else []
    board_id = board_values[0].get("id") if board_values else 1
    sprints = adapter.list_sprints(board_id=board_id)

    finished = datetime.utcnow().isoformat()

    return {
        "timestamps": {"started": started, "finished": finished},
        "webhook_registered": webhook_reg is not None,
        "webhook_result": webhook_reg,
        "issue": issue,
        "transition": transition_result,
        "comment": comment,
        "search": (
            {"issues_count": len(search.get("issues", []))} if isinstance(search, dict) else {"error": search_error}
        ),
        "jsm_request": jsm_request or {"skipped": True, "reason": "SUP project not present"},
        "agile_sprints": {"count": len(sprints.get("values", []))},
    }


if __name__ == "__main__":  # pragma: no cover
    result = main()
    print(json.dumps(result, indent=2, sort_keys=True))

