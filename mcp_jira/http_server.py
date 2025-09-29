"""HTTP bridge exposing Jira MCP tools over a simple JSON protocol."""

from __future__ import annotations

import argparse
import logging
import os
import threading
import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from .oauth import OAuthHandler, deliver_callback
from .server import get_tool, invoke_tool, list_tools
from .tools import refresh_adapter

LOGGER = logging.getLogger("mcp_jira.http_server")


class InvokePayload(BaseModel):
    """Request body for invoking a tool."""

    name: str = Field(..., description="Registered tool name")
    arguments: Dict[str, Any] | None = Field(
        default_factory=dict,
        description="Arguments to pass to the tool callable",
    )


def build_app() -> FastAPI:
    app = FastAPI(title="MCP Jira Bridge", version="1.0.0")

    oauth_handler: OAuthHandler | None = None
    oauth_ready = threading.Event()
    current_token = {"access_token": os.getenv("JIRA_TOKEN")}  # mutable holder

    def _update_from_payload(payload) -> None:
        if payload is None:
            return
        previous = current_token.get("access_token")
        if previous == getattr(payload, "access_token", None):
            # Still ensure base_url is correct, even if token did not change
            base_url = None
            if getattr(payload, "cloud_id", None):
                base_url = f"https://api.atlassian.com/ex/jira/{payload.cloud_id}"
            elif getattr(payload, "resource_url", None):
                base_url = payload.resource_url
            if base_url:
                os.environ["JIRA_BASE_URL"] = base_url
                refresh_adapter()
            return
        # Update token and base URL deterministically
        current_token["access_token"] = payload.access_token
        os.environ["JIRA_TOKEN"] = payload.access_token
        base_url = None
        if getattr(payload, "cloud_id", None):
            base_url = f"https://api.atlassian.com/ex/jira/{payload.cloud_id}"
        elif getattr(payload, "resource_url", None):
            base_url = payload.resource_url
        if base_url:
            os.environ["JIRA_BASE_URL"] = base_url
        refresh_adapter()

    def _ensure_runtime_token() -> None:
        if oauth_handler is None:
            return
        if not oauth_ready.wait(timeout=0):
            raise HTTPException(status_code=503, detail="OAuth authorization in progress")
        payload = oauth_handler.ensure_token()
        _update_from_payload(payload)

    @app.on_event("startup")
    def _startup() -> None:  # pragma: no cover - wiring
        nonlocal oauth_handler
        token = os.getenv("JIRA_TOKEN")
        if token:
            refresh_adapter()
            LOGGER.info("MCP Jira bridge ready (base_url=%s)", os.getenv("JIRA_BASE_URL"))
            return

        if os.getenv("ATLASSIAN_CLIENT_ID") and os.getenv("ATLASSIAN_CLIENT_SECRET"):
            oauth_handler = OAuthHandler.from_env()

            def _oauth_worker() -> None:
                while True:
                    try:
                        payload = oauth_handler.ensure_token()
                    except Exception as exc:  # pragma: no cover - interactive
                        LOGGER.error("OAuth flow failed: %s", exc)
                        time.sleep(5)
                        continue
                    _update_from_payload(payload)
                    oauth_ready.set()
                    LOGGER.info(
                        "MCP Jira bridge ready via OAuth (base_url=%s, cloud_id=%s)",
                        os.getenv("JIRA_BASE_URL"),
                        payload.cloud_id,
                    )
                    break

            threading.Thread(target=_oauth_worker, daemon=True).start()
            return

        LOGGER.error(
            "Missing credentials – set JIRA_TOKEN or ATLASSIAN_CLIENT_ID/SECRET before start"
        )
        raise RuntimeError("No Jira credentials configured")

    @app.get("/health", tags=["system"])
    def healthcheck() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/tools", tags=["tools"])
    def tools() -> Dict[str, Any]:
        return list_tools()

    @app.post("/tools/invoke", tags=["tools"])
    def invoke(payload: InvokePayload) -> Dict[str, Any]:
        try:
            tool = get_tool(payload.name)
        except KeyError as exc:  # pragma: no cover - thin wrapper
            raise HTTPException(status_code=404, detail=f"Unknown tool: {payload.name}") from exc

        arguments = payload.arguments or {}
        _ensure_runtime_token()
        try:
            result = invoke_tool(payload.name, arguments)
        except Exception as exc:  # pragma: no cover - propagate errors as HTTP 400
            LOGGER.exception("Tool %s raised an exception", payload.name)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result

    @app.get("/oauth/callback", tags=["oauth"])
    def oauth_callback(state: str, code: str | None = None, error: str | None = None) -> Dict[str, Any]:
        deliver_callback(state, code, error)
        if error:
            return {"status": "error", "detail": error}
        return {"status": "ok"}

    return app


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the MCP Jira HTTP bridge")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address")
    parser.add_argument("--port", type=int, default=8055, help="Bind port")
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "info"),
        help="Log level (debug, info, warning, error)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level.upper(), format="[%(levelname)s] %(message)s")

    app = build_app()
    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":  # pragma: no cover - CLI utility
    run()
