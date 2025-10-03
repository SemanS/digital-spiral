"""OAuth 2.0 flow for Jira Cloud."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """Base exception for OAuth errors."""
    pass


class OAuthStateError(OAuthError):
    """OAuth state mismatch error."""
    pass


class OAuthTokenError(OAuthError):
    """OAuth token error."""
    pass


class JiraOAuthClient:
    """
    OAuth 2.0 client for Jira Cloud.
    
    Implements the OAuth 2.0 authorization code flow for Jira Cloud apps.
    """

    # Jira OAuth endpoints
    AUTHORIZE_URL = "https://auth.atlassian.com/authorize"
    TOKEN_URL = "https://auth.atlassian.com/oauth/token"
    ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: list[str] | None = None,
    ):
        """
        Initialize OAuth client.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI after authorization
            scopes: List of OAuth scopes (default: read:jira-work, read:jira-user)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or [
            "read:jira-work",
            "read:jira-user",
            "write:jira-work",
            "offline_access",  # For refresh tokens
        ]

        self.http_client = httpx.AsyncClient()

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def generate_state(self) -> str:
        """
        Generate random state for CSRF protection.

        Returns:
            Random state string
        """
        return secrets.token_urlsafe(32)

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """
        Get authorization URL for user to grant access.

        Args:
            state: Optional state for CSRF protection (generated if not provided)

        Returns:
            Tuple of (authorization_url, state)
        """
        if state is None:
            state = self.generate_state()

        params = {
            "audience": "api.atlassian.com",
            "client_id": self.client_id,
            "scope": " ".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent",
        }

        auth_url = f"{self.AUTHORIZE_URL}?{urlencode(params)}"
        return auth_url, state

    async def exchange_code_for_token(
        self,
        code: str,
        state: str | None = None,
        expected_state: str | None = None,
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback
            state: State from callback
            expected_state: Expected state for validation

        Returns:
            Token response with access_token, refresh_token, expires_in, etc.

        Raises:
            OAuthStateError: If state doesn't match
            OAuthTokenError: If token exchange fails
        """
        # Validate state
        if expected_state and state != expected_state:
            raise OAuthStateError("State mismatch - possible CSRF attack")

        # Exchange code for token
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        try:
            response = await self.http_client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise OAuthTokenError(
                    f"Token exchange failed: {response.status_code} - {error_data}"
                )

            token_data = response.json()

            # Add expiration timestamp
            if "expires_in" in token_data:
                token_data["expires_at"] = (
                    datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
                ).isoformat()

            return token_data

        except httpx.HTTPError as e:
            raise OAuthTokenError(f"HTTP error during token exchange: {e}") from e

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            OAuthTokenError: If refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        try:
            response = await self.http_client.post(
                self.TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise OAuthTokenError(
                    f"Token refresh failed: {response.status_code} - {error_data}"
                )

            token_data = response.json()

            # Add expiration timestamp
            if "expires_in" in token_data:
                token_data["expires_at"] = (
                    datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
                ).isoformat()

            return token_data

        except httpx.HTTPError as e:
            raise OAuthTokenError(f"HTTP error during token refresh: {e}") from e

    async def get_accessible_resources(self, access_token: str) -> list[dict]:
        """
        Get list of Jira sites accessible with the access token.

        Args:
            access_token: OAuth access token

        Returns:
            List of accessible resources (Jira sites)

        Raises:
            OAuthTokenError: If request fails
        """
        try:
            response = await self.http_client.get(
                self.ACCESSIBLE_RESOURCES_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise OAuthTokenError(
                    f"Failed to get accessible resources: {response.status_code}"
                )

            return response.json()

        except httpx.HTTPError as e:
            raise OAuthTokenError(f"HTTP error getting accessible resources: {e}") from e

    def is_token_expired(self, token_data: dict) -> bool:
        """
        Check if access token is expired.

        Args:
            token_data: Token data with expires_at field

        Returns:
            True if expired, False otherwise
        """
        if "expires_at" not in token_data:
            return True

        expires_at = datetime.fromisoformat(token_data["expires_at"])
        # Consider token expired 5 minutes before actual expiration
        return datetime.utcnow() >= expires_at - timedelta(minutes=5)

    async def ensure_valid_token(self, token_data: dict) -> dict:
        """
        Ensure token is valid, refresh if needed.

        Args:
            token_data: Current token data

        Returns:
            Valid token data (refreshed if needed)

        Raises:
            OAuthTokenError: If refresh fails
        """
        if not self.is_token_expired(token_data):
            return token_data

        if "refresh_token" not in token_data:
            raise OAuthTokenError("Token expired and no refresh token available")

        logger.info("Access token expired, refreshing...")
        return await self.refresh_access_token(token_data["refresh_token"])


__all__ = [
    "JiraOAuthClient",
    "OAuthError",
    "OAuthStateError",
    "OAuthTokenError",
]

