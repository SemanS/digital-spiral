"""Observability infrastructure for Digital Spiral."""

from .logger import (
    LoggerAdapter,
    configure_logging,
    get_log_format,
    get_log_level,
    get_logger,
    redact_sensitive_data,
)
from .metrics import get_metrics
from .middleware import ObservabilityMiddleware, RequestContextMiddleware
from .tracing import (
    add_span_attributes,
    add_span_event,
    configure_tracing,
    get_current_span,
    get_tracer,
    record_exception,
    set_span_status,
)

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    "get_log_level",
    "get_log_format",
    "LoggerAdapter",
    "redact_sensitive_data",
    # Metrics
    "get_metrics",
    # Tracing
    "configure_tracing",
    "get_tracer",
    "get_current_span",
    "add_span_attributes",
    "add_span_event",
    "set_span_status",
    "record_exception",
    # Middleware
    "ObservabilityMiddleware",
    "RequestContextMiddleware",
]