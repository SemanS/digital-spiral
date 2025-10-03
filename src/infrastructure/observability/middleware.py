"""Observability middleware for FastAPI."""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import LoggerAdapter, get_logger
from .metrics import (
    http_request_duration_seconds,
    http_request_size_bytes,
    http_requests_total,
    http_response_size_bytes,
)
from .tracing import add_span_attributes, get_current_span

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding observability to FastAPI applications.

    Adds:
    - Request ID generation and propagation
    - Structured logging with context
    - Prometheus metrics
    - OpenTelemetry tracing attributes
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and add observability."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Add request ID to request state
        request.state.request_id = request_id

        # Create logger with context
        context_logger = LoggerAdapter(
            logger,
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        # Add tracing attributes
        span = get_current_span()
        if span.is_recording():
            add_span_attributes(
                {
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.route": request.url.path,
                    "http.request_id": request_id,
                }
            )

        # Log request
        context_logger.info(
            "Request started",
            extra={
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
        )

        # Record request size
        request_size = int(request.headers.get("content-length", 0))
        http_request_size_bytes.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(request_size)

        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)

            # Record response size
            response_size = int(response.headers.get("content-length", 0))
            http_response_size_bytes.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(response_size)

            # Add tracing attributes
            if span.is_recording():
                add_span_attributes(
                    {
                        "http.status_code": response.status_code,
                        "http.response_size": response_size,
                    }
                )

            # Log response
            context_logger.info(
                "Request completed",
                extra={
                    "status_code": response.status_code,
                    "duration_seconds": duration,
                    "response_size": response_size,
                },
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time

            # Record error metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)

            # Log error
            context_logger.error(
                "Request failed",
                extra={
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "duration_seconds": duration,
                },
                exc_info=True,
            )

            # Re-raise exception
            raise


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding request context to all requests.

    Extracts tenant_id, user_id, etc. from headers or JWT tokens
    and adds them to request state for use in logging and tracing.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and add context."""
        # Extract tenant ID from header or path
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            request.state.tenant_id = tenant_id

        # Extract user ID from header (would typically come from JWT)
        user_id = request.headers.get("X-User-ID")
        if user_id:
            request.state.user_id = user_id

        # Add context to tracing
        span = get_current_span()
        if span.is_recording():
            if tenant_id:
                add_span_attributes({"tenant.id": tenant_id})
            if user_id:
                add_span_attributes({"user.id": user_id})

        return await call_next(request)


__all__ = [
    "ObservabilityMiddleware",
    "RequestContextMiddleware",
]

