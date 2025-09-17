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
_JQL_GTE_PATTERN = re.compile(r"^(?P<field>[\w.]+)\s*>=\s*(?P<value>.+)$")


def parse_jql(jql: str | None) -> dict[str, Any]:
    """Parse a small, opinionated subset of JQL.

    Returns a dictionary with ``filters`` and ``order_by`` keys. The ``filters``
    mapping contains normalised field/value pairs for equality and IN clauses.
    ``date_filters`` carries comparison operators (currently ``>=`` for
    ``created`` and ``updated``). ``order_by`` is a list of ``(field,
    direction)`` tuples in declaration order.
    """

    if not jql:
        return {"filters": {}, "order_by": []}
    raw = jql.strip()
    if not raw:
        return {"filters": {}, "order_by": []}

    parts = re.split(r"\s+ORDER\s+BY\s+", raw, maxsplit=1, flags=re.IGNORECASE)
    filter_part = parts[0].strip()
    order_part = parts[1].strip() if len(parts) == 2 else ""

    filters: dict[str, Any] = {}
    date_filters: dict[str, dict[str, str]] = {}
    if filter_part:
        clauses = re.split(r"\s+AND\s+", filter_part, flags=re.IGNORECASE)
    else:
        clauses = []
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
        gte_match = _JQL_GTE_PATTERN.match(clause)
        if gte_match:
            field = gte_match.group("field").lower()
            if field not in {"updated", "created"}:
                raise ValueError(f"Unsupported JQL clause: {clause}")
            value = _normalise_value(gte_match.group("value"))
            date_filters.setdefault(field, {})["gte"] = value
            continue
        eq_match = _JQL_EQUALS_PATTERN.match(clause)
        if eq_match:
            field = eq_match.group("field").lower()
            value = _normalise_value(eq_match.group("value"))
            filters[field] = value
            continue
        raise ValueError(f"Unsupported JQL clause: {clause}")

    order_by: list[tuple[str, str]] = []
    if order_part:
        for segment in order_part.split(","):
            segment = segment.strip()
            if not segment:
                continue
            tokens = segment.split()
            field = tokens[0]
            if len(tokens) == 1:
                if field.lower() == "updated":
                    direction = "DESC"
                else:
                    direction = "ASC"
            elif len(tokens) == 2 and tokens[1].upper() in {"ASC", "DESC"}:
                direction = tokens[1].upper()
            else:
                raise ValueError(f"Unsupported ORDER BY clause: {segment}")
            order_by.append((field.lower(), direction.lower()))

    return {"filters": filters, "order_by": order_by, "date_filters": date_filters}


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
