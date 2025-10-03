"""Prometheus metrics configuration."""

from __future__ import annotations

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
)


# ============================================================================
# HTTP Metrics
# ============================================================================

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

http_request_size_bytes = Summary(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Summary(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)

# ============================================================================
# Database Metrics
# ============================================================================

db_queries_total = Counter(
    "db_queries_total",
    "Total database queries",
    ["operation", "table"],
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Number of idle database connections",
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"],
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)

cache_operations_duration_seconds = Histogram(
    "cache_operations_duration_seconds",
    "Cache operation duration in seconds",
    ["operation", "cache_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)

# ============================================================================
# Jira API Metrics
# ============================================================================

jira_api_requests_total = Counter(
    "jira_api_requests_total",
    "Total Jira API requests",
    ["method", "endpoint", "status"],
)

jira_api_request_duration_seconds = Histogram(
    "jira_api_request_duration_seconds",
    "Jira API request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

jira_api_rate_limit_remaining = Gauge(
    "jira_api_rate_limit_remaining",
    "Remaining Jira API rate limit",
    ["instance_id"],
)

jira_api_errors_total = Counter(
    "jira_api_errors_total",
    "Total Jira API errors",
    ["method", "endpoint", "error_type"],
)

# ============================================================================
# Sync Metrics
# ============================================================================

sync_operations_total = Counter(
    "sync_operations_total",
    "Total sync operations",
    ["instance_id", "operation_type", "status"],
)

sync_duration_seconds = Histogram(
    "sync_duration_seconds",
    "Sync operation duration in seconds",
    ["instance_id", "operation_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0),
)

sync_items_processed = Counter(
    "sync_items_processed",
    "Total items processed during sync",
    ["instance_id", "item_type"],
)

sync_errors_total = Counter(
    "sync_errors_total",
    "Total sync errors",
    ["instance_id", "error_type"],
)

# ============================================================================
# AI Metrics
# ============================================================================

ai_requests_total = Counter(
    "ai_requests_total",
    "Total AI requests",
    ["provider", "model", "operation"],
)

ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider", "model"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

ai_tokens_used = Counter(
    "ai_tokens_used",
    "Total AI tokens used",
    ["provider", "model", "token_type"],
)

ai_cost_usd = Counter(
    "ai_cost_usd",
    "Total AI cost in USD",
    ["provider", "model"],
)

ai_errors_total = Counter(
    "ai_errors_total",
    "Total AI errors",
    ["provider", "model", "error_type"],
)

# ============================================================================
# Business Metrics
# ============================================================================

issues_processed_total = Counter(
    "issues_processed_total",
    "Total issues processed",
    ["instance_id", "project_key"],
)

webhooks_received_total = Counter(
    "webhooks_received_total",
    "Total webhooks received",
    ["instance_id", "event_type"],
)

webhooks_processing_duration_seconds = Histogram(
    "webhooks_processing_duration_seconds",
    "Webhook processing duration in seconds",
    ["instance_id", "event_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
)

# ============================================================================
# System Metrics
# ============================================================================

background_tasks_active = Gauge(
    "background_tasks_active",
    "Number of active background tasks",
    ["task_type"],
)

background_tasks_completed_total = Counter(
    "background_tasks_completed_total",
    "Total completed background tasks",
    ["task_type", "status"],
)


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest(REGISTRY)


__all__ = [
    # HTTP
    "http_requests_total",
    "http_request_duration_seconds",
    "http_request_size_bytes",
    "http_response_size_bytes",
    # Database
    "db_queries_total",
    "db_query_duration_seconds",
    "db_connections_active",
    "db_connections_idle",
    # Cache
    "cache_hits_total",
    "cache_misses_total",
    "cache_operations_duration_seconds",
    # Jira API
    "jira_api_requests_total",
    "jira_api_request_duration_seconds",
    "jira_api_rate_limit_remaining",
    "jira_api_errors_total",
    # Sync
    "sync_operations_total",
    "sync_duration_seconds",
    "sync_items_processed",
    "sync_errors_total",
    # AI
    "ai_requests_total",
    "ai_request_duration_seconds",
    "ai_tokens_used",
    "ai_cost_usd",
    "ai_errors_total",
    # Business
    "issues_processed_total",
    "webhooks_received_total",
    "webhooks_processing_duration_seconds",
    # System
    "background_tasks_active",
    "background_tasks_completed_total",
    # Utility
    "get_metrics",
]

