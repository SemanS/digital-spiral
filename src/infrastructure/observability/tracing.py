"""OpenTelemetry tracing configuration."""

from __future__ import annotations

import os
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def get_service_name() -> str:
    """
    Get service name from environment variable.

    Returns:
        Service name (default: digital-spiral)
    """
    return os.getenv("SERVICE_NAME", "digital-spiral")


def get_environment() -> str:
    """
    Get environment from environment variable.

    Returns:
        Environment (default: development)
    """
    return os.getenv("ENVIRONMENT", "development")


def get_otlp_endpoint() -> str | None:
    """
    Get OTLP exporter endpoint from environment variable.

    Returns:
        OTLP endpoint URL or None if not configured
    """
    return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")


def configure_tracing(
    service_name: str | None = None,
    environment: str | None = None,
    otlp_endpoint: str | None = None,
    enable_console_export: bool = False,
) -> TracerProvider:
    """
    Configure OpenTelemetry tracing.

    Args:
        service_name: Service name (defaults to SERVICE_NAME env var)
        environment: Environment (defaults to ENVIRONMENT env var)
        otlp_endpoint: OTLP exporter endpoint (defaults to OTEL_EXPORTER_OTLP_ENDPOINT env var)
        enable_console_export: Whether to export traces to console (for debugging)

    Returns:
        TracerProvider instance
    """
    if service_name is None:
        service_name = get_service_name()

    if environment is None:
        environment = get_environment()

    if otlp_endpoint is None:
        otlp_endpoint = get_otlp_endpoint()

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "2.0.0",
            "deployment.environment": environment,
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter if endpoint is configured
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Add console exporter for debugging
    if enable_console_export:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    return provider


def get_tracer(name: str) -> trace.Tracer:
    """
    Get tracer instance.

    Args:
        name: Tracer name (usually __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def get_current_span() -> trace.Span:
    """
    Get current active span.

    Returns:
        Current span
    """
    return trace.get_current_span()


def add_span_attributes(attributes: dict[str, Any]) -> None:
    """
    Add attributes to current span.

    Args:
        attributes: Dictionary of attributes to add
    """
    span = get_current_span()
    if span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict[str, Any] | None = None) -> None:
    """
    Add event to current span.

    Args:
        name: Event name
        attributes: Optional event attributes
    """
    span = get_current_span()
    if span.is_recording():
        span.add_event(name, attributes or {})


def set_span_status(status_code: trace.StatusCode, description: str | None = None) -> None:
    """
    Set status of current span.

    Args:
        status_code: Status code (OK, ERROR, UNSET)
        description: Optional status description
    """
    span = get_current_span()
    if span.is_recording():
        from opentelemetry.trace import Status

        span.set_status(Status(status_code, description))


def record_exception(exception: Exception, escaped: bool = False) -> None:
    """
    Record exception in current span.

    Args:
        exception: Exception to record
        escaped: Whether the exception escaped the span scope
    """
    span = get_current_span()
    if span.is_recording():
        span.record_exception(exception, escaped=escaped)


__all__ = [
    "configure_tracing",
    "get_tracer",
    "get_current_span",
    "add_span_attributes",
    "add_span_event",
    "set_span_status",
    "record_exception",
]

