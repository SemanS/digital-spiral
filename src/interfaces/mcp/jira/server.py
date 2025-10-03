"""MCP Jira SSE server implementation."""

import asyncio
import json
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_session

from .errors import MCPException
from .tools import TOOL_REGISTRY, MCPContext

app = FastAPI(title="MCP Jira Server", version="1.0.0")


class ToolInvokeRequest(BaseModel):
    """Request to invoke a tool."""

    name: str
    arguments: dict


class ToolInvokeResponse(BaseModel):
    """Response from tool invocation."""

    result: dict
    request_id: str
    timestamp: str


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
    # For now, get from header
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant ID")

    try:
        return UUID(tenant_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid tenant ID")


def get_user_from_auth(request: Request) -> Optional[str]:
    """Extract user ID from authentication.

    Args:
        request: FastAPI request

    Returns:
        User ID or None
    """
    # TODO: Implement proper authentication
    return request.headers.get("X-User-ID")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "server": "mcp-jira",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "sse": "/sse",
            "invoke": "/tools/invoke",
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
                    "server": "mcp-jira",
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


@app.post("/tools/invoke")
async def invoke_tool(
    request: Request,
    body: ToolInvokeRequest,
    session: AsyncSession = Depends(get_session),
):
    """Invoke MCP tool (fallback to POST).

    Args:
        request: FastAPI request
        body: Tool invocation request
        session: Database session

    Returns:
        Tool result or error
    """
    # Authenticate
    tenant_id = get_tenant_from_auth(request)
    user_id = get_user_from_auth(request)
    request_id = str(uuid4())

    # Get tool
    tool_func = TOOL_REGISTRY.get(body.name)
    if not tool_func:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{body.name}' not found",
        )

    # Create context
    context = MCPContext(
        session=session,
        tenant_id=tenant_id,
        user_id=user_id,
        request_id=request_id,
    )

    try:
        # Parse parameters based on tool
        # This is a simplified version - in production, you'd want proper schema validation
        params = body.arguments

        # Execute tool
        result = await tool_func(params, context)

        # Commit transaction
        await session.commit()

        return ToolInvokeResponse(
            result=result.dict() if hasattr(result, "dict") else result,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
        )

    except ValidationError as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail={
                "code": "validation_error",
                "message": "Invalid parameters",
                "errors": e.errors(),
            },
        )

    except MCPException as e:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail=e.to_error().dict(),
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "code": "internal_error",
                "message": str(e),
                "request_id": request_id,
            },
        )


@app.get("/tools")
async def list_tools():
    """List available tools.

    Returns:
        List of available tool names
    """
    return {
        "tools": list(TOOL_REGISTRY.keys()),
        "count": len(TOOL_REGISTRY),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8055)

