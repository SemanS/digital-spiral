"""Utility helpers for the mock Jira server."""

from __future__ import annotations

import re
from typing import Any, Iterable

from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Domain-specific error for returning Jira-style error payloads."""

    def __init__(
        self,
        status: int,
        message: str,
        field_errors: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status = status
        self.message = message
        self.field_errors = field_errors or {}
        self.headers = headers or {}
        super().__init__(message)

    def to_response(self) -> JSONResponse:
        response = error_response(self.status, self.message, self.field_errors)
        for key, value in self.headers.items():
            response.headers[key] = value
        return response


_JQL_IN_PATTERN = re.compile(r"^(?P<field>[\w.]+)\s+IN\s*\((?P<values>[^)]*)\)$", re.IGNORECASE)
_JQL_EQUALS_PATTERN = re.compile(r"^(?P<field>[\w.]+)\s*=\s*(?P<value>.+)$")


def parse_jql(jql: str | None) -> dict[str, Any]:
    """Parse a very small subset of JQL into a dictionary of filters."""

    if not jql:
        return {}
    raw = jql.strip()
    if not raw:
        return {}

    # Ignore ORDER BY clause.
    raw = raw.split("ORDER BY", 1)[0].strip()

    filters: dict[str, Any] = {}
    clauses = re.split(r"\s+AND\s+", raw, flags=re.IGNORECASE)
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue
        in_match = _JQL_IN_PATTERN.match(clause)
        if in_match:
            field = in_match.group("field").lower()
            values = [
                _normalise_value(v)
                for v in in_match.group("values").split(",")
                if v.strip()
            ]
            filters[field] = values
            continue
        eq_match = _JQL_EQUALS_PATTERN.match(clause)
        if eq_match:
            field = eq_match.group("field").lower()
            value = _normalise_value(eq_match.group("value"))
            filters[field] = value
            continue
        raise ValueError(f"Unsupported JQL clause: {clause}")
    return filters


def _normalise_value(raw: str) -> str:
    value = raw.strip()
    if value.startswith("\"") and value.endswith("\""):
        value = value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        value = value[1:-1]
    return value


def paginate(items: Iterable[Any], start_at: int, max_results: int) -> dict[str, Any]:
    sequence = list(items)
    total = len(sequence)
    start_at = max(start_at, 0)
    max_results = max(0, max_results)
    page = sequence[start_at : start_at + max_results] if max_results else []
    is_last = start_at + len(page) >= total
    return {
        "startAt": start_at,
        "maxResults": max_results,
        "total": total,
        "isLast": is_last,
        "values": page,
    }


def error_response(
    status: int, message: str, field_errors: dict[str, str] | None = None
) -> JSONResponse:
    """Return a JSONResponse carrying the Jira-style error payload."""

    return JSONResponse(
        status_code=status,
        content={
            "errorMessages": [message],
            "errors": field_errors or {},
        },
    )
