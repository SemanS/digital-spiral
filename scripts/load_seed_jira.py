#!/usr/bin/env python3
"""Import seed data into a Jira instance via the MCP bridge."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict

import requests

DEFAULT_ENDPOINT = "http://127.0.0.1:8055/tools/invoke"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load issues/comments from a seed JSON using MCP tools"
    )
    parser.add_argument(
        "seed",
        help="Path to seed JSON (output of generate_dummy_jira.py)",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"MCP invoke endpoint (default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        metavar="SRC=DST",
        help="Map seed project keys to target project keys (can repeat)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned operations without executing them",
    )
    parser.add_argument(
        "--skip-missing-users",
        action="store_true",
        help="Ignore assignee/accountId values that are not recognized",
    )
    parser.add_argument(
        "--skip-custom-fields",
        action="store_true",
        help="Do not attempt to set customfield_* values from the seed",
    )
    parser.add_argument(
        "--skip-assignee",
        action="store_true",
        help="Do not set assignee from the seed data",
    )
    parser.add_argument(
        "--issuetype",
        action="append",
        default=[],
        metavar="SEED=TARGET",
        help="Map seed issue type names to target Jira issue type names",
    )
    parser.add_argument(
        "--default-issuetype",
        help="Fallback target issue type name when no mapping is found",
    )
    return parser.parse_args(argv)


def build_project_map(pairs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in pairs:
        if "=" not in entry:
            raise ValueError(f"Invalid project mapping '{entry}', expected SRC=DST")
        src, dst = entry.split("=", 1)
        mapping[src.strip()] = dst.strip()
    return mapping


def build_type_map(pairs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in pairs:
        if "=" not in entry:
            raise ValueError(f"Invalid issue type mapping '{entry}', expected SEED=TARGET")
        src, dst = entry.split("=", 1)
        mapping[src.strip()] = dst.strip()
    return mapping


def read_token_payload() -> dict[str, Any]:
    token_path = Path.home() / ".config" / "mcp-jira" / "token.json"
    if not token_path.exists():
        raise RuntimeError(
            "Token file ~/.config/mcp-jira/token.json not found. Run run_mcp_jira_oauth.py first."
        )
    return json.loads(token_path.read_text(encoding="utf-8"))


def fetch_site_issue_types(access_token: str, cloud_id: str) -> dict[str, list[dict[str, Any]]]:
    base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}"
    response = requests.get(
        f"{base_url}/rest/api/3/issuetype",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    result: dict[str, list[dict[str, Any]]] = {}
    for entry in response.json():
        result.setdefault(entry["name"], []).append(
            {
                "id": entry["id"],
                "subtask": entry.get("subtask", False),
            }
        )
    return result


def resolve_issue_type(
    site_types: dict[str, list[dict[str, Any]]],
    type_expr: str,
) -> dict[str, Any] | None:
    name = type_expr
    id_hint = None
    if "@" in type_expr:
        name, id_hint = type_expr.split("@", 1)
    name = name.strip()
    candidates = site_types.get(name)
    if not candidates:
        return None
    if not id_hint:
        return next((c for c in candidates if not c.get("subtask")), candidates[0])
    for candidate in candidates:
        if candidate.get("id") == id_hint.strip():
            return candidate
    return None


def invoke_tool(endpoint: str, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"name": name, "arguments": arguments}
    response = requests.post(endpoint, json=payload, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(
            f"Tool '{name}' failed ({response.status_code}): {response.text.strip()}"
        )
    return response.json()


def build_fields(
    issue: Dict[str, Any],
    skip_missing_users: bool,
    skip_custom_fields: bool,
    skip_assignee: bool,
) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    if issue.get("assignee_id") and not skip_assignee:
        assignee = {"accountId": issue["assignee_id"]}
        if skip_missing_users:
            assignee["skip"] = True  # downstream tooling may honour this hint
        fields["assignee"] = assignee
    if issue.get("labels"):
        fields["labels"] = list(issue["labels"])
    if not skip_custom_fields and issue.get("custom_fields"):
        fields.update(issue["custom_fields"])
    if issue.get("sprint_id") and not skip_custom_fields:
        fields.setdefault("customfield_10020", []).append(issue["sprint_id"])
    return fields


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    project_map = build_project_map(args.project)
    type_map = build_type_map(args.issuetype)

    with open(args.seed, "r", encoding="utf-8") as handle:
        seed = json.load(handle)

    issues: list[dict[str, Any]] = seed.get("issues", [])
    if not issues:
        print("No issues found in seed", file=sys.stderr)
        return

    seed_type_name = {item["id"]: item["name"] for item in seed.get("issue_types", [])}
    token_payload = read_token_payload()
    access_token = token_payload.get("access_token")
    cloud_id = token_payload.get("cloud_id")
    if not access_token or not cloud_id:
        raise RuntimeError("Token payload missing access_token or cloud_id")
    site_issue_types = fetch_site_issue_types(access_token, cloud_id)

    mapping: dict[str, str] = {}
    stats = defaultdict(int)

    for issue in issues:
        source_key = issue.get("key", "<unknown>")
        target_project = project_map.get(issue["project_key"], issue["project_key"])

        seed_type_id = issue.get("issue_type_id")
        seed_type_name_value = seed_type_name.get(seed_type_id, seed_type_id)
        target_expr = type_map.get(seed_type_name_value, seed_type_name_value)
        target_type_info = resolve_issue_type(site_issue_types, target_expr)
        if not target_type_info:
            if args.default_issuetype:
                target_type_info = resolve_issue_type(site_issue_types, args.default_issuetype)
            if not target_type_info:
                print(
                    f"  ! skipping {source_key}: issue type '{seed_type_name_value}' not available",
                    file=sys.stderr,
                )
                stats["failed_type"] += 1
                continue
        if target_type_info.get("subtask"):
            print(
                f"  ! skipping {source_key}: resolved issue type '{target_expr}' is a sub-task",
                file=sys.stderr,
            )
            stats["failed_type"] += 1
            continue

        create_args: dict[str, Any] = {
            "project_key": target_project,
            "issue_type_id": target_type_info["id"],
            "summary": issue["summary"],
        }
        if issue.get("description"):
            create_args["description_adf"] = issue["description"]

        fields = build_fields(
            issue,
            args.skip_missing_users,
            args.skip_custom_fields,
            args.skip_assignee,
        )
        if fields:
            create_args["fields"] = fields

        print(f"Creating issue {source_key} -> project {target_project}…")
        if args.dry_run:
            continue

        try:
            created = invoke_tool(args.endpoint, "jira.create_issue", create_args)
        except Exception as exc:  # pragma: no cover - runtime feedback
            print(f"  ! failed to create {source_key}: {exc}", file=sys.stderr)
            stats["failed"] += 1
            continue

        new_key = created.get("key") or source_key
        mapping[source_key] = new_key
        stats["created"] += 1

        for comment in issue.get("comments", []):
            body = comment.get("body")
            if not body:
                continue
            try:
                invoke_tool(
                    args.endpoint,
                    "jira.add_comment",
                    {"key": new_key, "body_adf": body},
                )
            except Exception as exc:  # pragma: no cover - runtime feedback
                print(f"  ! failed to add comment to {new_key}: {exc}", file=sys.stderr)
                stats["comment_failed"] += 1
            else:
                stats["comments"] += 1

    print("\nImport summary:")
    for key, value in sorted(stats.items()):
        print(f"  {key}: {value}")

    if mapping:
        print("\nIssue key mapping (seed -> created):")
        for src, dst in mapping.items():
            print(f"  {src} -> {dst}")


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
