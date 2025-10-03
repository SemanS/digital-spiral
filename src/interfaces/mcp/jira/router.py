"""FastAPI router for MCP Jira endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_session

from .server import ToolInvokeRequest, invoke_tool, list_tools, sse_endpoint

router = APIRouter(prefix="/mcp/jira", tags=["MCP Jira"])

# Add routes
router.add_api_route("/sse", sse_endpoint, methods=["GET"])
router.add_api_route("/tools/invoke", invoke_tool, methods=["POST"])
router.add_api_route("/tools", list_tools, methods=["GET"])

__all__ = ["router"]

