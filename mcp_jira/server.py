"""Lightweight facade exposing Jira adapter tools for MCP integrations."""

from __future__ import annotations

from typing import Any, Dict

from .tools import TOOL_REGISTRY


def get_tool(name: str):
    """Return a registered MCP tool callable by name."""

    return TOOL_REGISTRY[name]


def invoke_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke a tool with the provided arguments."""

    return TOOL_REGISTRY[name](args)


def list_tools() -> Dict[str, Any]:
    """Return the metadata describing available tools."""

    return {
        name: {
            "doc": func.__doc__,
        }
        for name, func in TOOL_REGISTRY.items()
    }
