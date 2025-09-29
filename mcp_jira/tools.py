"""Convenience tools for bridging the Jira adapter into MCP workflows."""

from __future__ import annotations

import os
from typing import Any, Callable, Dict

from clients.python.jira_adapter import JiraAdapter

__all__ = [
    "ADAPTER",
    "refresh_adapter",
    "t_jira_create_issue",
    "t_jira_get_issue",
    "t_jira_search",
    "t_jira_list_transitions",
    "t_jira_transition_issue",
    "t_jira_add_comment",
    "t_jsm_create_request",
    "t_agile_list_sprints",
    # new tools
    "t_jira_list_projects",
    "t_jira_list_issue_types",
    "t_jira_create_issue_by_type_name",
    "TOOL_REGISTRY",
]


def _build_adapter() -> JiraAdapter:
    base_url = os.getenv("JIRA_BASE_URL", "http://localhost:9000")
    token = os.getenv("JIRA_TOKEN", "mock-token")
    timeout = float(os.getenv("JIRA_TIMEOUT", "10"))
    user_agent = os.getenv("JIRA_USER_AGENT", "MockJiraAdapter/1.0")
    return JiraAdapter(base_url, token, timeout=timeout, user_agent=user_agent)


ADAPTER = _build_adapter()


def refresh_adapter() -> JiraAdapter:
    """Rebuild the global adapter after environment changes."""

    global ADAPTER
    ADAPTER = _build_adapter()
    return ADAPTER


def t_jira_create_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    return ADAPTER.create_issue(
        args["project_key"],
        args["issue_type_id"],
        args["summary"],
        args.get("description_adf"),
        args.get("fields"),
    )


def t_jira_get_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    return ADAPTER.get_issue(args["key"])


def t_jira_search(args: Dict[str, Any]) -> Dict[str, Any]:
    return ADAPTER.search(
        args["jql"],
        args.get("start_at", 0),
        args.get("max_results", 50),
    )


def t_jira_list_transitions(args: Dict[str, Any]) -> Dict[str, Any]:
    return {"transitions": ADAPTER.list_transitions(args["key"])}


def t_jira_transition_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    return ADAPTER.transition_issue(args["key"], args["transition_id"])


def t_jira_add_comment(args: Dict[str, Any]) -> Dict[str, Any]:
    return ADAPTER.add_comment(args["key"], args["body_adf"])


def t_jsm_create_request(args: Dict[str, Any]) -> Dict[str, Any]:
    return ADAPTER.create_request(
        args["service_desk_id"],
        args["request_type_id"],
        args["summary"],
        args.get("fields"),
    )


def t_agile_list_sprints(args: Dict[str, Any]) -> Dict[str, Any]:
    return ADAPTER.list_sprints(
        args["board_id"],
        args.get("start_at", 0),
        args.get("max_results", 50),
    )


# --- Additional convenience tools for real Jira via MCP ---

def t_jira_list_projects(args: Dict[str, Any]) -> Dict[str, Any]:
    """List projects available to the current credentials."""
    projects = ADAPTER._call("GET", "/rest/api/3/project")
    return {"projects": projects}


def t_jira_list_issue_types(args: Dict[str, Any]) -> Dict[str, Any]:
    """List issue types in the current site (name, id, subtask)."""
    types = ADAPTER._call("GET", "/rest/api/3/issuetype")
    return {"issuetypes": types}


def _resolve_issue_type_id_by_name(name: str) -> str:
    """Resolve an issue type ID by display name. Supports 'Name@id' hint."""
    raw = name.strip()
    if "@" in raw:
        base, id_hint = raw.split("@", 1)
        return id_hint.strip() or base.strip()
    types = ADAPTER._call("GET", "/rest/api/3/issuetype") or []
    lowered = raw.lower()
    # Prefer non-subtask match; fallback to any name match; finally first entry
    candidates = [t for t in types if str(t.get("name", "")).lower() == lowered]
    non_sub = next((t for t in candidates if not bool(t.get("subtask"))), None)
    chosen = non_sub or (candidates[0] if candidates else (types[0] if types else None))
    if not chosen or not chosen.get("id"):
        raise RuntimeError(f"Cannot resolve issue type id for '{name}'")
    return str(chosen["id"])


def t_jira_create_issue_by_type_name(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create issue resolving type by name (e.g., 'Task' or 'Task@10001')."""
    type_name = args["issue_type_name"]
    type_id = _resolve_issue_type_id_by_name(type_name)
    return ADAPTER.create_issue(
        args["project_key"],
        type_id,
        args["summary"],
        args.get("description_adf"),
        args.get("fields"),
    )


TOOL_REGISTRY: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "jira.create_issue": t_jira_create_issue,
    "jira.get_issue": t_jira_get_issue,
    "jira.search": t_jira_search,
    "jira.list_transitions": t_jira_list_transitions,
    "jira.transition_issue": t_jira_transition_issue,
    "jira.add_comment": t_jira_add_comment,
    "jsm.create_request": t_jsm_create_request,
    "agile.list_sprints": t_agile_list_sprints,
    # new entries
    "jira.list_projects": t_jira_list_projects,
    "jira.list_issue_types": t_jira_list_issue_types,
    "jira.create_issue_by_type_name": t_jira_create_issue_by_type_name,
}
