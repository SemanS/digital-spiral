"""Structured logging configuration."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["timestamp"] = self.formatTime(record, self.datefmt)

        # Add context fields if present
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        if hasattr(record, "tenant_id"):
            log_record["tenant_id"] = record.tenant_id

        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id

        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id

        if hasattr(record, "span_id"):
            log_record["span_id"] = record.span_id


def get_log_level() -> int:
    """
    Get log level from environment variable.

    Returns:
        Log level (default: INFO)
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def get_log_format() -> str:
    """
    Get log format from environment variable.

    Returns:
        Log format: 'json' or 'text' (default: json)
    """
    return os.getenv("LOG_FORMAT", "json").lower()


def configure_logging(
    level: int | None = None,
    format_type: str | None = None,
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (defaults to LOG_LEVEL env var)
        format_type: Format type ('json' or 'text', defaults to LOG_FORMAT env var)
    """
    if level is None:
        level = get_log_level()

    if format_type is None:
        format_type = get_log_format()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Set formatter based on format type
    if format_type == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        # Text format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for adding context to log records.

    Example:
        ```python
        logger = get_logger(__name__)
        context_logger = LoggerAdapter(logger, {
            "request_id": "req-123",
            "tenant_id": "tenant-456",
        })
        context_logger.info("Processing request")
        ```
    """

    def process(
        self,
        msg: str,
        kwargs: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Add context to log record."""
        # Add extra fields to the log record
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def redact_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Redact sensitive data from log messages.

    Args:
        data: Data dictionary

    Returns:
        Redacted data dictionary
    """
    sensitive_keys = {
        "password",
        "token",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "credentials",
        "credit_card",
        "ssn",
    }

    redacted = {}
    for key, value in data.items():
        key_lower = key.lower()

        # First check if value is a dict or list (recurse into it)
        if isinstance(value, dict):
            # Recurse into nested dict
            redacted[key] = redact_sensitive_data(value)
        elif isinstance(value, list):
            # Recurse into list items
            redacted[key] = [
                redact_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        # Then check if key contains sensitive information
        elif any(sensitive in key_lower for sensitive in sensitive_keys):
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value

    return redacted


__all__ = [
    "configure_logging",
    "get_logger",
    "get_log_level",
    "get_log_format",
    "LoggerAdapter",
    "redact_sensitive_data",
]

