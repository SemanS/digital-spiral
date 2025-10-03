"""Error schemas and exceptions for MCP Jira."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MCPErrorCode(str, Enum):
    """Error codes for MCP operations."""

    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    UPSTREAM_4XX = "upstream_4xx"
    UPSTREAM_5XX = "upstream_5xx"
    CONFLICT = "conflict"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"


class MCPError(BaseModel):
    """Standard error response for MCP operations."""

    code: MCPErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None  # Seconds (for rate_limited)
    request_id: str  # For tracing
    timestamp: datetime


class MCPException(Exception):
    """Base exception for MCP operations."""

    def __init__(
        self,
        code: MCPErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.retry_after = retry_after
        self.request_id = request_id or self._generate_request_id()
        self.timestamp = datetime.utcnow()
        super().__init__(message)

    def to_error(self) -> MCPError:
        """Convert exception to error model."""
        return MCPError(
            code=self.code,
            message=self.message,
            details=self.details,
            retry_after=self.retry_after,
            request_id=self.request_id,
            timestamp=self.timestamp,
        )

    @staticmethod
    def _generate_request_id() -> str:
        """Generate a unique request ID."""
        import uuid

        return f"req_{uuid.uuid4().hex[:12]}"


class ValidationError(MCPException):
    """Validation error exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=MCPErrorCode.VALIDATION_ERROR, message=message, details=details
        )


class RateLimitError(MCPException):
    """Rate limit exceeded exception."""

    def __init__(
        self, message: str, retry_after: int, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            code=MCPErrorCode.RATE_LIMITED,
            message=message,
            details=details,
            retry_after=retry_after,
        )


class NotFoundError(MCPException):
    """Resource not found exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(code=MCPErrorCode.NOT_FOUND, message=message, details=details)


class UnauthorizedError(MCPException):
    """Unauthorized access exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code=MCPErrorCode.UNAUTHORIZED, message=message, details=details
        )


class UpstreamError(MCPException):
    """Upstream service error exception."""

    def __init__(
        self,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
    ):
        code = (
            MCPErrorCode.UPSTREAM_5XX
            if status_code >= 500
            else MCPErrorCode.UPSTREAM_4XX
        )
        super().__init__(code=code, message=message, details=details)


__all__ = [
    "MCPErrorCode",
    "MCPError",
    "MCPException",
    "ValidationError",
    "RateLimitError",
    "NotFoundError",
    "UnauthorizedError",
    "UpstreamError",
]

