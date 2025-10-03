"""Jira API client."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class JiraAPIError(Exception):
    """Base exception for Jira API errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class JiraAuthenticationError(JiraAPIError):
    """Jira authentication error."""
    pass


class JiraRateLimitError(JiraAPIError):
    """Jira rate limit exceeded."""
    pass


class JiraNotFoundError(JiraAPIError):
    """Jira resource not found."""
    pass


class JiraClient:
    """
    Jira REST API client.
    
    Provides methods for interacting with Jira Cloud REST API v3.
    Includes authentication, rate limiting, and error handling.
    """

    def __init__(
        self,
        base_url: str,
        email: str | None = None,
        api_token: str | None = None,
        access_token: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize Jira API client.

        Args:
            base_url: Jira instance base URL (e.g., "https://your-domain.atlassian.net")
            email: User email for basic auth
            api_token: API token for basic auth
            access_token: OAuth 2.0 access token
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Set up authentication
        if access_token:
            # OAuth 2.0
            self.auth = None
            self.headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        elif email and api_token:
            # Basic auth
            self.auth = (email, api_token)
            self.headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        else:
            raise ValueError("Either access_token or (email, api_token) must be provided")

        # Create HTTP client
        self.client = httpx.AsyncClient(
            auth=self.auth,
            headers=self.headers,
            timeout=timeout,
        )

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _make_url(self, path: str) -> str:
        """
        Create full URL from path.

        Args:
            path: API path (e.g., "/rest/api/3/issue/PROJ-123")

        Returns:
            Full URL
        """
        if not path.startswith("/"):
            path = f"/{path}"
        return urljoin(self.base_url, path)

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
        **kwargs,
    ) -> dict | list:
        """
        Make HTTP request to Jira API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path
            params: Query parameters
            json: JSON body
            **kwargs: Additional arguments for httpx

        Returns:
            Response JSON

        Raises:
            JiraAPIError: On API errors
        """
        url = self._make_url(path)

        logger.debug(f"Jira API request: {method} {url}")

        try:
            response = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                **kwargs,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise JiraRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds",
                    status_code=429,
                )

            # Handle authentication errors
            if response.status_code == 401:
                raise JiraAuthenticationError(
                    "Authentication failed. Check credentials.",
                    status_code=401,
                )

            # Handle not found
            if response.status_code == 404:
                raise JiraNotFoundError(
                    f"Resource not found: {path}",
                    status_code=404,
                )

            # Handle other errors
            if response.status_code >= 400:
                error_data = None
                try:
                    error_data = response.json()
                except Exception:
                    pass

                raise JiraAPIError(
                    f"Jira API error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                    response=error_data,
                )

            # Parse response
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Jira API timeout: {url}")
            raise JiraAPIError(f"Request timeout: {url}") from e

        except httpx.NetworkError as e:
            logger.error(f"Jira API network error: {url}")
            raise JiraAPIError(f"Network error: {url}") from e

    async def get(self, path: str, params: dict | None = None) -> dict | list:
        """
        Make GET request.

        Args:
            path: API path
            params: Query parameters

        Returns:
            Response JSON
        """
        return await self._request("GET", path, params=params)

    async def post(self, path: str, json: dict | None = None) -> dict:
        """
        Make POST request.

        Args:
            path: API path
            json: JSON body

        Returns:
            Response JSON
        """
        return await self._request("POST", path, json=json)

    async def put(self, path: str, json: dict | None = None) -> dict:
        """
        Make PUT request.

        Args:
            path: API path
            json: JSON body

        Returns:
            Response JSON
        """
        return await self._request("PUT", path, json=json)

    async def delete(self, path: str) -> dict:
        """
        Make DELETE request.

        Args:
            path: API path

        Returns:
            Response JSON
        """
        return await self._request("DELETE", path)

    # ============================================================================
    # Convenience methods for common Jira API endpoints
    # ============================================================================

    async def get_myself(self) -> dict:
        """
        Get current user information.

        Returns:
            User data
        """
        return await self.get("/rest/api/3/myself")

    async def get_issue(self, issue_key: str, expand: list[str] | None = None) -> dict:
        """
        Get issue by key.

        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            expand: Fields to expand (e.g., ["changelog", "renderedFields"])

        Returns:
            Issue data
        """
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        return await self.get(f"/rest/api/3/issue/{issue_key}", params=params)

    async def search_issues(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: list[str] | None = None,
        expand: list[str] | None = None,
    ) -> dict:
        """
        Search issues using JQL.

        Args:
            jql: JQL query string
            start_at: Starting index
            max_results: Maximum results to return
            fields: Fields to include
            expand: Fields to expand

        Returns:
            Search results
        """
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
        }

        if fields:
            params["fields"] = ",".join(fields)

        if expand:
            params["expand"] = ",".join(expand)

        return await self.get("/rest/api/3/search", params=params)

    async def get_project(self, project_key: str, expand: list[str] | None = None) -> dict:
        """
        Get project by key.

        Args:
            project_key: Project key (e.g., "PROJ")
            expand: Fields to expand

        Returns:
            Project data
        """
        params = {}
        if expand:
            params["expand"] = ",".join(expand)

        return await self.get(f"/rest/api/3/project/{project_key}", params=params)

    async def get_all_projects(
        self,
        start_at: int = 0,
        max_results: int = 50,
    ) -> list[dict]:
        """
        Get all projects.

        Args:
            start_at: Starting index
            max_results: Maximum results to return

        Returns:
            List of projects
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }

        result = await self.get("/rest/api/3/project/search", params=params)
        return result.get("values", [])

    async def get_user(self, account_id: str, expand: list[str] | None = None) -> dict:
        """
        Get user by account ID.

        Args:
            account_id: User account ID
            expand: Fields to expand

        Returns:
            User data
        """
        params = {"accountId": account_id}
        if expand:
            params["expand"] = ",".join(expand)

        return await self.get("/rest/api/3/user", params=params)

    async def get_issue_comments(
        self,
        issue_key: str,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict:
        """
        Get comments for an issue.

        Args:
            issue_key: Issue key
            start_at: Starting index
            max_results: Maximum results to return

        Returns:
            Comments data
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }

        return await self.get(f"/rest/api/3/issue/{issue_key}/comment", params=params)

    async def get_issue_changelog(
        self,
        issue_key: str,
        start_at: int = 0,
        max_results: int = 50,
    ) -> dict:
        """
        Get changelog for an issue.

        Args:
            issue_key: Issue key
            start_at: Starting index
            max_results: Maximum results to return

        Returns:
            Changelog data
        """
        params = {
            "startAt": start_at,
            "maxResults": max_results,
        }

        return await self.get(f"/rest/api/3/issue/{issue_key}/changelog", params=params)

    async def get_all_issue_types(self) -> list[dict]:
        """
        Get all issue types.

        Returns:
            List of issue types
        """
        return await self.get("/rest/api/3/issuetype")

    async def get_all_priorities(self) -> list[dict]:
        """
        Get all priorities.

        Returns:
            List of priorities
        """
        return await self.get("/rest/api/3/priority")

    async def get_all_statuses(self) -> list[dict]:
        """
        Get all statuses.

        Returns:
            List of statuses
        """
        return await self.get("/rest/api/3/status")


__all__ = [
    "JiraClient",
    "JiraAPIError",
    "JiraAuthenticationError",
    "JiraRateLimitError",
    "JiraNotFoundError",
]

