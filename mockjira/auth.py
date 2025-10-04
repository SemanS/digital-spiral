"""Authentication and rate limiting helpers."""

from __future__ import annotations

from typing import Callable

from fastapi import Header, Request, status

from .store import InMemoryStore, RateLimitError
from .utils import ApiError


async def get_current_user(  # pragma: no cover - replaced during app setup
    authorization: str | None = Header(default=None),
    x_force_429: str | None = Header(default=None),
) -> str:
    raise RuntimeError("Authentication dependency not configured")


def auth_dependency(store: InMemoryStore) -> Callable:
    """Return a dependency enforcing bearer token auth and rate limiting."""

    async def dependency(
        request: Request,
        authorization: str | None = Header(default=None),
        x_force_429: str | None = Header(default=None),
    ) -> str:
        if authorization is None:
            raise ApiError(
                status=status.HTTP_401_UNAUTHORIZED,
                message="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer, Basic"},
            )

        # Support both Bearer token and Basic auth
        token = None
        if authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
        elif authorization.startswith("Basic "):
            # For Basic auth, accept any credentials and use first token
            # In real implementation, you'd validate email/password
            token = list(store.tokens.keys())[0] if store.tokens else None

        if not token or not store.is_valid_token(token):
            raise ApiError(
                status=status.HTTP_401_UNAUTHORIZED,
                message="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer, Basic"},
            )
        if x_force_429 and store.should_force_429(token):
            raise ApiError(
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                message="Simulated rate limit",
                headers={"Retry-After": "1"},
            )
        try:
            cost = _request_cost(request)
            store.register_call(token, cost=cost)
        except RateLimitError as exc:  # pragma: no cover - protective branch
            headers = {"Retry-After": str(exc.retry_after)}
            if exc.remaining is not None:
                headers["X-RateLimit-Remaining"] = str(exc.remaining)
            if exc.reset_at is not None:
                headers["X-RateLimit-Reset"] = str(exc.reset_at)
            raise ApiError(
                status=status.HTTP_429_TOO_MANY_REQUESTS,
                message="Rate limit exceeded",
                headers=headers,
            ) from exc
        return store.tokens[token]

    return dependency


def _request_cost(request: Request) -> int:
    """Return an approximate request cost for the rate limiter."""

    path = request.url.path
    if path.endswith("/search"):
        return 5
    if request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        return 2
    return 1
