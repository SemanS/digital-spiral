"""OAuth 2.0 helper utilities for authenticating Jira API requests."""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests

AUTH_BASE_URL = "https://auth.atlassian.com"
ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"
DEFAULT_SCOPES = [
    "offline_access",
    "read:jira-user",
    "read:jira-work",
    "write:jira-work",
    "manage:jira-project",
]


def _default_token_path() -> Path:
    base = os.getenv("MCP_JIRA_TOKEN_PATH")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".config" / "mcp-jira" / "token.json"


@dataclass(slots=True)
class TokenPayload:
    access_token: str
    expires_at: float
    refresh_token: Optional[str] = None
    cloud_id: Optional[str] = None
    resource_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "expires_at": self.expires_at,
            "refresh_token": self.refresh_token,
            "cloud_id": self.cloud_id,
            "resource_url": self.resource_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        return cls(
            access_token=data["access_token"],
            expires_at=float(data["expires_at"]),
            refresh_token=data.get("refresh_token"),
            cloud_id=data.get("cloud_id"),
            resource_url=data.get("resource_url"),
        )


class TokenStore:
    """Persist token payloads on disk."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _default_token_path()
        self._lock = threading.Lock()

    def load(self) -> Optional[TokenPayload]:
        with self._lock:
            if not self.path.exists():
                return None
            try:
                data = json.loads(self.path.read_text("utf-8"))
            except Exception:
                return None
        try:
            return TokenPayload.from_dict(data)
        except Exception:
            return None

    def save(self, payload: TokenPayload) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload.to_dict(), indent=2), encoding="utf-8")
            tmp.replace(self.path)


class OAuthSession:
    """Track a single OAuth authorization flow awaiting callback."""

    def __init__(self, state: str) -> None:
        self.state = state
        self.event = threading.Event()
        self.code: Optional[str] = None
        self.error: Optional[str] = None

    def deliver(self, code: Optional[str], error: Optional[str]) -> None:
        self.code = code
        self.error = error
        self.event.set()


class OAuthRegistry:
    """Manage outstanding OAuth sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, OAuthSession] = {}
        self._lock = threading.Lock()

    def create(self) -> OAuthSession:
        state = secrets.token_urlsafe(16)
        session = OAuthSession(state)
        with self._lock:
            self._sessions[state] = session
        return session

    def deliver(self, state: str, code: Optional[str], error: Optional[str]) -> None:
        with self._lock:
            session = self._sessions.get(state)
        if not session:
            return
        session.deliver(code, error)
        with self._lock:
            self._sessions.pop(state, None)


REGISTRY = OAuthRegistry()


class OAuthHandler:
    """High-level orchestrator for acquiring Jira access tokens."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: list[str] | None = None,
        token_store: TokenStore | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or DEFAULT_SCOPES
        self.token_store = token_store or TokenStore()

    @classmethod
    def from_env(cls) -> "OAuthHandler":
        client_id = os.getenv("ATLASSIAN_CLIENT_ID")
        client_secret = os.getenv("ATLASSIAN_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError("ATLASSIAN_CLIENT_ID/SECRET must be set for OAuth flow")
        redirect_uri = os.getenv("ATLASSIAN_REDIRECT_URI", "http://127.0.0.1:8055/oauth/callback")
        raw_scopes = os.getenv("ATLASSIAN_SCOPES")
        scopes = raw_scopes.split() if raw_scopes else None
        return cls(client_id, client_secret, redirect_uri, scopes)

    def ensure_token(self) -> TokenPayload:
        current = self.token_store.load()
        if current:
            if current.expires_at - 60 > time.time():
                return current
            if current.refresh_token:
                refreshed = self._refresh(current.refresh_token)
                enriched = self._augment_with_resource(refreshed)
                self.token_store.save(enriched)
                return enriched

        session = REGISTRY.create()
        authorize_url = self._authorize_url(session.state)
        print("\n=== Atlassian OAuth 2.0 ===")
        print("Open the following URL in your browser and authorize access:")
        print(authorize_url)
        print("Waiting for authorization callback...")

        if not session.event.wait(timeout=300):
            raise RuntimeError("OAuth authorization timed out")
        if session.error:
            raise RuntimeError(f"OAuth authorization failed: {session.error}")
        if not session.code:
            raise RuntimeError("OAuth callback did not provide an authorization code")

        token = self._exchange_code(session.code)
        enriched = self._augment_with_resource(token)
        self.token_store.save(enriched)
        return enriched

    def _authorize_url(self, state: str) -> str:
        scope_param = "%20".join(self.scopes)
        return (
            f"{AUTH_BASE_URL}/authorize?audience=api.atlassian.com"
            f"&client_id={self.client_id}"
            f"&scope={scope_param}"
            f"&redirect_uri={self.redirect_uri}"
            f"&state={state}"
            f"&response_type=code"
            f"&prompt=consent"
        )

    def _exchange_code(self, code: str) -> TokenPayload:
        response = requests.post(
            f"{AUTH_BASE_URL}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return TokenPayload(
            access_token=data["access_token"],
            expires_at=time.time() + float(data.get("expires_in", 3600)),
            refresh_token=data.get("refresh_token"),
        )

    def _refresh(self, refresh_token: str) -> TokenPayload:
        response = requests.post(
            f"{AUTH_BASE_URL}/oauth/token",
            json={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return TokenPayload(
            access_token=data["access_token"],
            expires_at=time.time() + float(data.get("expires_in", 3600)),
            refresh_token=data.get("refresh_token", refresh_token),
        )

    def _augment_with_resource(self, token: TokenPayload) -> TokenPayload:
        headers = {"Authorization": f"Bearer {token.access_token}"}
        response = requests.get(ACCESSIBLE_RESOURCES_URL, headers=headers, timeout=30)
        response.raise_for_status()
        resources = response.json()
        if not resources:
            return token

        desired_url = os.getenv("JIRA_BASE_URL")
        chosen: Dict[str, Any] | None = None
        if desired_url:
            for resource in resources:
                if resource.get("url") == desired_url.rstrip("/"):
                    chosen = resource
                    break
        if chosen is None:
            chosen = resources[0]

        token.cloud_id = chosen.get("id")
        token.resource_url = chosen.get("url")

        # OAuth 2.0 requests must target api.atlassian.com/ex/jira/{cloud_id}
        if token.cloud_id:
            api_base = f"https://api.atlassian.com/ex/jira/{token.cloud_id}"
            os.environ["JIRA_BASE_URL"] = api_base
        elif token.resource_url:
            os.environ["JIRA_BASE_URL"] = token.resource_url
        elif desired_url:
            os.environ["JIRA_BASE_URL"] = desired_url

        return token


def deliver_callback(state: str, code: Optional[str], error: Optional[str]) -> None:
    """Utility used by the HTTP bridge callback endpoint."""

    REGISTRY.deliver(state, code, error)


__all__ = [
    "OAuthHandler",
    "TokenPayload",
    "TokenStore",
    "deliver_callback",
]
