"""OpenTelemetry tracing service for Digital Spiral."""

from contextlib import contextmanager
from typing import Any, Dict, Optional
from uuid import UUID

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode


class TracingService:
    """Service for distributed tracing with OpenTelemetry."""

    def __init__(
        self,
        service_name: str = "digital-spiral",
        otlp_endpoint: Optional[str] = None,
        enabled: bool = True,
    ):
        """Initialize tracing service.

        Args:
            service_name: Service name for traces
            otlp_endpoint: OTLP collector endpoint (e.g., "localhost:4317")
            enabled: Whether tracing is enabled
        """
        self.service_name = service_name
        self.enabled = enabled
        
        if enabled:
            # Create resource
            resource = Resource.create({
                "service.name": service_name,
                "service.version": "1.0.0",
            })
            
            # Create tracer provider
            provider = TracerProvider(resource=resource)
            
            # Add OTLP exporter if endpoint provided
            if otlp_endpoint:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            
            # Set global tracer provider
            trace.set_tracer_provider(provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Trace an operation.

        Args:
            operation_name: Name of the operation
            attributes: Additional attributes to add to the span

        Yields:
            Span object

        Example:
            >>> with tracing.trace_operation("fetch_issues", {"project": "PROJ"}):
            ...     issues = await fetch_issues()
        """
        if not self.enabled:
            yield None
            return
        
        with self.tracer.start_as_current_span(operation_name) as span:
            # Add attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            try:
                yield span
            except Exception as e:
                # Record exception
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def trace_http_request(
        self,
        method: str,
        url: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
    ):
        """Trace an HTTP request.

        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            duration_ms: Request duration in milliseconds
        """
        if not self.enabled:
            return
        
        with self.tracer.start_as_current_span("http.request") as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.url", url)
            
            if status_code:
                span.set_attribute("http.status_code", status_code)
            
            if duration_ms:
                span.set_attribute("http.duration_ms", duration_ms)

    def trace_database_query(
        self,
        query_type: str,
        table: str,
        duration_ms: Optional[float] = None,
        rows_affected: Optional[int] = None,
    ):
        """Trace a database query.

        Args:
            query_type: Query type (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
        """
        if not self.enabled:
            return
        
        with self.tracer.start_as_current_span("db.query") as span:
            span.set_attribute("db.operation", query_type)
            span.set_attribute("db.table", table)
            
            if duration_ms:
                span.set_attribute("db.duration_ms", duration_ms)
            
            if rows_affected is not None:
                span.set_attribute("db.rows_affected", rows_affected)

    def trace_tool_invocation(
        self,
        tool_name: str,
        tenant_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        success: Optional[bool] = None,
    ):
        """Trace an MCP tool invocation.

        Args:
            tool_name: Tool name
            tenant_id: Tenant ID
            user_id: User ID
            duration_ms: Execution duration in milliseconds
            success: Whether execution was successful
        """
        if not self.enabled:
            return
        
        with self.tracer.start_as_current_span("mcp.tool.invoke") as span:
            span.set_attribute("mcp.tool.name", tool_name)
            
            if tenant_id:
                span.set_attribute("tenant.id", str(tenant_id))
            
            if user_id:
                span.set_attribute("user.id", user_id)
            
            if duration_ms:
                span.set_attribute("mcp.tool.duration_ms", duration_ms)
            
            if success is not None:
                span.set_attribute("mcp.tool.success", success)

    def trace_adapter_operation(
        self,
        adapter_type: str,
        operation: str,
        instance_id: Optional[UUID] = None,
        duration_ms: Optional[float] = None,
        success: Optional[bool] = None,
    ):
        """Trace a source adapter operation.

        Args:
            adapter_type: Adapter type (jira, github, asana, etc.)
            operation: Operation name (fetch, create, update, etc.)
            instance_id: Instance ID
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
        """
        if not self.enabled:
            return
        
        with self.tracer.start_as_current_span("adapter.operation") as span:
            span.set_attribute("adapter.type", adapter_type)
            span.set_attribute("adapter.operation", operation)
            
            if instance_id:
                span.set_attribute("adapter.instance_id", str(instance_id))
            
            if duration_ms:
                span.set_attribute("adapter.duration_ms", duration_ms)
            
            if success is not None:
                span.set_attribute("adapter.success", success)

    def add_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Add an event to the current span.

        Args:
            name: Event name
            attributes: Event attributes
        """
        if not self.enabled:
            return
        
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes or {})

    def set_attribute(self, key: str, value: Any):
        """Set an attribute on the current span.

        Args:
            key: Attribute key
            value: Attribute value
        """
        if not self.enabled:
            return
        
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, str(value))

    def record_exception(self, exception: Exception):
        """Record an exception in the current span.

        Args:
            exception: Exception to record
        """
        if not self.enabled:
            return
        
        span = trace.get_current_span()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))


# Global tracing service instance
_tracing_service: Optional[TracingService] = None


def get_tracing_service(
    service_name: str = "digital-spiral",
    otlp_endpoint: Optional[str] = None,
    enabled: bool = True,
) -> TracingService:
    """Get global tracing service instance.

    Args:
        service_name: Service name for traces
        otlp_endpoint: OTLP collector endpoint
        enabled: Whether tracing is enabled

    Returns:
        TracingService instance
    """
    global _tracing_service
    if _tracing_service is None:
        _tracing_service = TracingService(
            service_name=service_name,
            otlp_endpoint=otlp_endpoint,
            enabled=enabled,
        )
    return _tracing_service


# Convenience instance
tracing = get_tracing_service()


__all__ = [
    "TracingService",
    "get_tracing_service",
    "tracing",
]

