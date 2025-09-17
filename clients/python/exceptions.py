"""Exception hierarchy for the Jira adapter client."""

from __future__ import annotations


class JiraError(Exception):
    """Base class for Jira-related errors."""


class JiraBadRequest(JiraError):
    """400 Bad Request."""


class JiraUnauthorized(JiraError):
    """401/403 Unauthorized or forbidden."""


class JiraNotFound(JiraError):
    """404 Not Found."""


class JiraConflict(JiraError):
    """409 Conflict."""


class JiraRateLimited(JiraError):
    """429 Too Many Requests."""

    def __init__(self, retry_after: float | None = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.retry_after = retry_after


class JiraServerError(JiraError):
    """5xx Server error."""
