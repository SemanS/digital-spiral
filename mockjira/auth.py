"""Authentication and rate limiting helpers."""

from __future__ import annotations

from typing import Callable

from fastapi import Header, HTTPException, status

from .store import InMemoryStore, RateLimitError


async def get_current_user(  # pragma: no cover - replaced during app setup
    authorization: str | None = Header(default=None),
    x_force_429: str | None = Header(default=None),
) -> str:
    raise RuntimeError("Authentication dependency not configured")


def auth_dependency(store: InMemoryStore) -> Callable:
    """Return a dependency enforcing bearer token auth and rate limiting."""

    async def dependency(
        authorization: str | None = Header(default=None),
        x_force_429: str | None = Header(default=None),
    ) -> str:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = authorization.split(" ", 1)[1]
        if not store.is_valid_token(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if x_force_429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Simulated rate limit",
                headers={"Retry-After": "5"},
            )
        try:
            store.register_call(token)
        except RateLimitError as exc:  # pragma: no cover - protective branch
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": str(exc.retry_after)},
            ) from exc
        return store.tokens[token]

    return dependency
