#!/usr/bin/env python3
"""Helper script for exercising the MCP Jira bridge."""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Invoke a Jira MCP tool via the local bridge")
    parser.add_argument(
        "tool",
        nargs="?",
        default="jira.search",
        help="Registered tool name (default: jira.search)",
    )
    parser.add_argument(
        "--args-json",
        default="{\"jql\": \"project = DOC\"}",
        help="JSON string with tool arguments",
    )
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8055/tools/invoke",
        help="Bridge invoke endpoint (default: http://127.0.0.1:8055/tools/invoke)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON response",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload: dict[str, Any] = {
            "name": args.tool,
            "arguments": json.loads(args.args_json),
        }
    except json.JSONDecodeError as exc:  # pragma: no cover - CLI validation
        raise SystemExit(f"Invalid JSON for --args-json: {exc}")

    response = requests.post(args.url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()

    if args.pretty:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps(data))


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
