"""MCP SQL SSE server implementation."""

import asyncio
import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_session

from .templates import QUERY_TEMPLATES, execute_template

app = FastAPI(title="MCP SQL Server", version="1.0.0")


class QueryRequest(BaseModel):
    """Request to execute a query template."""

    template_name: str
    params: dict


def get_tenant_from_auth(request: Request) -> UUID:
    """Extract tenant ID from authentication.

    Args:
        request: FastAPI request

    Returns:
        Tenant ID

    Raises:
        HTTPException: If authentication fails
    """
    # TODO: Implement proper authentication
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant ID")

    try:
        return UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid tenant ID")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "server": "mcp-sql",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "sse": "/sse",
            "query": "/query",
            "templates": "/templates",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol.

    Args:
        request: FastAPI request

    Returns:
        EventSourceResponse with SSE stream
    """
    # Authenticate
    try:
        tenant_id = get_tenant_from_auth(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail},
        )

    async def event_generator():
        """Generate SSE events."""
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps(
                {
                    "server": "mcp-sql",
                    "version": "1.0.0",
                    "tenant_id": str(tenant_id),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        }

        # Heartbeat every 30 seconds
        while True:
            if await request.is_disconnected():
                break

            yield {
                "event": "heartbeat",
                "data": json.dumps({"timestamp": datetime.utcnow().isoformat()}),
            }

            await asyncio.sleep(30)

    return EventSourceResponse(event_generator())


@app.post("/query")
async def execute_query(
    request: Request,
    body: QueryRequest,
    session: AsyncSession = Depends(get_session),
):
    """Execute a SQL query template.

    Args:
        request: FastAPI request
        body: Query request
        session: Database session

    Returns:
        Query results
    """
    # Authenticate
    tenant_id = get_tenant_from_auth(request)

    # Add tenant_id to params
    params = body.params.copy()
    params["tenant_id"] = str(tenant_id)

    try:
        # Execute template
        result = await execute_template(
            session=session,
            template_name=body.template_name,
            params=params,
        )

        return result

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "validation_error",
                "message": "Invalid parameters",
                "errors": e.errors(),
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "invalid_template",
                "message": str(e),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "internal_error",
                "message": str(e),
            },
        )


@app.get("/templates")
async def list_templates():
    """List available query templates.

    Returns:
        List of available template names
    """
    return {
        "templates": list(QUERY_TEMPLATES.keys()),
        "count": len(QUERY_TEMPLATES),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8056)

