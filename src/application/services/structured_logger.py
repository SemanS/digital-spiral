"""Structured logging service for Digital Spiral."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID


class StructuredLogger:
    """Structured logger that outputs JSON logs."""

    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        include_timestamp: bool = True,
        include_level: bool = True,
    ):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Logging level
            include_timestamp: Include timestamp in logs
            include_level: Include log level in logs
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add JSON handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)

    def _build_log_entry(
        self,
        level: str,
        message: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Build structured log entry.

        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields

        Returns:
            Log entry dict
        """
        entry = {"message": message}
        
        if self.include_timestamp:
            entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        if self.include_level:
            entry["level"] = level
        
        # Add all additional fields
        entry.update(kwargs)
        
        return entry

    def debug(self, message: str, **kwargs):
        """Log debug message.

        Args:
            message: Log message
            **kwargs: Additional fields
        """
        entry = self._build_log_entry("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(entry))

    def info(self, message: str, **kwargs):
        """Log info message.

        Args:
            message: Log message
            **kwargs: Additional fields
        """
        entry = self._build_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(entry))

    def warning(self, message: str, **kwargs):
        """Log warning message.

        Args:
            message: Log message
            **kwargs: Additional fields
        """
        entry = self._build_log_entry("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(entry))

    def error(self, message: str, **kwargs):
        """Log error message.

        Args:
            message: Log message
            **kwargs: Additional fields
        """
        entry = self._build_log_entry("ERROR", message, **kwargs)
        self.logger.error(json.dumps(entry))

    def critical(self, message: str, **kwargs):
        """Log critical message.

        Args:
            message: Log message
            **kwargs: Additional fields
        """
        entry = self._build_log_entry("CRITICAL", message, **kwargs)
        self.logger.critical(json.dumps(entry))

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs,
    ):
        """Log HTTP request.

        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            tenant_id: Tenant ID
            user_id: User ID
            request_id: Request ID
            **kwargs: Additional fields
        """
        self.info(
            "HTTP request",
            event="http_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            tenant_id=str(tenant_id) if tenant_id else None,
            user_id=user_id,
            request_id=request_id,
            **kwargs,
        )

    def log_tool_invocation(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        error: Optional[str] = None,
        **kwargs,
    ):
        """Log MCP tool invocation.

        Args:
            tool_name: Tool name
            duration_ms: Execution duration in milliseconds
            success: Whether execution was successful
            tenant_id: Tenant ID
            user_id: User ID
            request_id: Request ID
            error: Error message if failed
            **kwargs: Additional fields
        """
        self.info(
            f"Tool invocation: {tool_name}",
            event="tool_invocation",
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success,
            tenant_id=str(tenant_id) if tenant_id else None,
            user_id=user_id,
            request_id=request_id,
            error=error,
            **kwargs,
        )

    def log_database_query(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        rows_affected: Optional[int] = None,
        **kwargs,
    ):
        """Log database query.

        Args:
            query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
            **kwargs: Additional fields
        """
        self.debug(
            f"Database query: {query_type} {table}",
            event="database_query",
            query_type=query_type,
            table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            **kwargs,
        )

    def log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        tenant_id: UUID,
        user_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """Log audit event.

        Args:
            action: Action performed (create, update, delete)
            resource_type: Resource type
            resource_id: Resource ID
            tenant_id: Tenant ID
            user_id: User ID
            changes: Changes made
            **kwargs: Additional fields
        """
        self.info(
            f"Audit: {action} {resource_type}",
            event="audit",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=str(tenant_id),
            user_id=user_id,
            changes=changes,
            **kwargs,
        )

    def log_error_with_context(
        self,
        error: Exception,
        context: Dict[str, Any],
        **kwargs,
    ):
        """Log error with context.

        Args:
            error: Exception
            context: Error context
            **kwargs: Additional fields
        """
        self.error(
            f"Error: {str(error)}",
            event="error",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            **kwargs,
        )


class JsonFormatter(logging.Formatter):
    """JSON formatter for logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON string
        """
        # If message is already JSON, return it
        if record.msg.startswith("{"):
            return record.msg
        
        # Otherwise, create JSON log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: int = logging.INFO) -> StructuredLogger:
    """Get or create a structured logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]


# Convenience loggers
app_logger = get_logger("digital_spiral")
mcp_logger = get_logger("digital_spiral.mcp")
db_logger = get_logger("digital_spiral.db", level=logging.DEBUG)
audit_logger = get_logger("digital_spiral.audit")


__all__ = [
    "StructuredLogger",
    "JsonFormatter",
    "get_logger",
    "app_logger",
    "mcp_logger",
    "db_logger",
    "audit_logger",
]

