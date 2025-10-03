# Observability Infrastructure

This directory contains observability infrastructure for Digital Spiral, including logging, metrics, and tracing.

## Overview

The observability layer provides:
- **Structured logging** with JSON format
- **Prometheus metrics** for monitoring
- **OpenTelemetry tracing** for distributed tracing
- **Request context** propagation
- **Sensitive data redaction**

## Components

### 1. Logging (`logger.py`)

Structured logging with JSON format and context propagation.

**Features**:
- JSON or text format (configurable via `LOG_FORMAT` env var)
- Log levels (configurable via `LOG_LEVEL` env var)
- Request ID, tenant ID, user ID propagation
- Sensitive data redaction
- Logger adapter for adding context

**Usage**:

```python
from src.infrastructure.observability import configure_logging, get_logger

# Configure logging (call once at startup)
configure_logging()

# Get logger
logger = get_logger(__name__)

# Log messages
logger.info("Processing request", extra={"request_id": "req-123"})
logger.error("Failed to process", exc_info=True)

# Use logger adapter for context
from src.infrastructure.observability import LoggerAdapter

context_logger = LoggerAdapter(logger, {
    "request_id": "req-123",
    "tenant_id": "tenant-456",
})
context_logger.info("Processing started")
```

**Redacting Sensitive Data**:

```python
from src.infrastructure.observability import redact_sensitive_data

data = {
    "username": "john",
    "password": "secret123",  # Will be redacted
    "api_key": "key123",      # Will be redacted
}

safe_data = redact_sensitive_data(data)
logger.info("User data", extra=safe_data)
```

### 2. Metrics (`metrics.py`)

Prometheus metrics for monitoring application performance.

**Available Metrics**:

**HTTP Metrics**:
- `http_requests_total` - Total HTTP requests (counter)
- `http_request_duration_seconds` - Request duration (histogram)
- `http_request_size_bytes` - Request size (summary)
- `http_response_size_bytes` - Response size (summary)

**Database Metrics**:
- `db_queries_total` - Total database queries (counter)
- `db_query_duration_seconds` - Query duration (histogram)
- `db_connections_active` - Active connections (gauge)
- `db_connections_idle` - Idle connections (gauge)

**Cache Metrics**:
- `cache_hits_total` - Cache hits (counter)
- `cache_misses_total` - Cache misses (counter)
- `cache_operations_duration_seconds` - Operation duration (histogram)

**Jira API Metrics**:
- `jira_api_requests_total` - Total Jira API requests (counter)
- `jira_api_request_duration_seconds` - Request duration (histogram)
- `jira_api_rate_limit_remaining` - Remaining rate limit (gauge)
- `jira_api_errors_total` - Total errors (counter)

**Sync Metrics**:
- `sync_operations_total` - Total sync operations (counter)
- `sync_duration_seconds` - Sync duration (histogram)
- `sync_items_processed` - Items processed (counter)
- `sync_errors_total` - Sync errors (counter)

**AI Metrics**:
- `ai_requests_total` - Total AI requests (counter)
- `ai_request_duration_seconds` - Request duration (histogram)
- `ai_tokens_used` - Tokens used (counter)
- `ai_cost_usd` - Cost in USD (counter)
- `ai_errors_total` - AI errors (counter)

**Usage**:

```python
from src.infrastructure.observability.metrics import (
    http_requests_total,
    http_request_duration_seconds,
)

# Increment counter
http_requests_total.labels(
    method="GET",
    endpoint="/api/issues",
    status="200",
).inc()

# Record histogram
http_request_duration_seconds.labels(
    method="GET",
    endpoint="/api/issues",
).observe(0.123)
```

**Exposing Metrics**:

```python
from fastapi import FastAPI, Response
from src.infrastructure.observability.metrics import get_metrics

app = FastAPI()

@app.get("/metrics")
def metrics():
    return Response(content=get_metrics(), media_type="text/plain")
```

### 3. Tracing (`tracing.py`)

OpenTelemetry distributed tracing.

**Features**:
- OTLP exporter support
- Automatic span creation
- Span attributes and events
- Exception recording

**Usage**:

```python
from src.infrastructure.observability import (
    configure_tracing,
    get_tracer,
    add_span_attributes,
)

# Configure tracing (call once at startup)
configure_tracing()

# Get tracer
tracer = get_tracer(__name__)

# Create span
with tracer.start_as_current_span("process_issue") as span:
    # Add attributes
    add_span_attributes({
        "issue.key": "PROJ-123",
        "issue.status": "Done",
    })
    
    # Do work
    process_issue()
```

### 4. Middleware (`middleware.py`)

FastAPI middleware for automatic observability.

**Features**:
- Request ID generation and propagation
- Automatic logging with context
- Automatic metrics recording
- Automatic tracing attributes

**Usage**:

```python
from fastapi import FastAPI
from src.infrastructure.observability.middleware import (
    ObservabilityMiddleware,
    RequestContextMiddleware,
)

app = FastAPI()

# Add middleware
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(RequestContextMiddleware)
```

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json         # json or text

# Tracing
SERVICE_NAME=digital-spiral
ENVIRONMENT=production
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

### Startup Configuration

```python
from src.infrastructure.observability import configure_logging, configure_tracing

# Configure logging
configure_logging()

# Configure tracing
configure_tracing()
```

## Best Practices

### 1. Structured Logging

Always use structured logging with extra fields:

```python
# Good
logger.info("User logged in", extra={
    "user_id": user.id,
    "ip_address": request.client.host,
})

# Bad
logger.info(f"User {user.id} logged in from {request.client.host}")
```

### 2. Metric Labels

Keep metric labels low cardinality:

```python
# Good
http_requests_total.labels(method="GET", endpoint="/api/issues", status="200")

# Bad (high cardinality)
http_requests_total.labels(method="GET", endpoint=f"/api/issues/{issue_id}", status="200")
```

### 3. Tracing

Add meaningful attributes to spans:

```python
with tracer.start_as_current_span("sync_issues") as span:
    add_span_attributes({
        "instance.id": instance_id,
        "sync.type": "incremental",
        "sync.items": len(issues),
    })
```

### 4. Error Handling

Always log errors with context:

```python
try:
    process_issue(issue)
except Exception as exc:
    logger.error(
        "Failed to process issue",
        extra={
            "issue_key": issue.key,
            "error": str(exc),
        },
        exc_info=True,
    )
    raise
```

## Monitoring

### Prometheus Queries

**Request rate**:
```promql
rate(http_requests_total[5m])
```

**Error rate**:
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

**P95 latency**:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Cache hit rate**:
```promql
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/)

