"""Unit tests for metrics."""

from __future__ import annotations

import pytest

from src.infrastructure.observability.metrics import (
    cache_hits_total,
    cache_misses_total,
    db_queries_total,
    get_metrics,
    http_requests_total,
    jira_api_requests_total,
)


class TestMetrics:
    """Tests for Prometheus metrics."""

    def test_http_requests_total(self):
        """Test HTTP requests counter."""
        initial_value = http_requests_total.labels(
            method="GET",
            endpoint="/api/issues",
            status="200",
        )._value.get()

        http_requests_total.labels(
            method="GET",
            endpoint="/api/issues",
            status="200",
        ).inc()

        new_value = http_requests_total.labels(
            method="GET",
            endpoint="/api/issues",
            status="200",
        )._value.get()

        assert new_value == initial_value + 1

    def test_db_queries_total(self):
        """Test database queries counter."""
        initial_value = db_queries_total.labels(
            operation="SELECT",
            table="issues",
        )._value.get()

        db_queries_total.labels(
            operation="SELECT",
            table="issues",
        ).inc()

        new_value = db_queries_total.labels(
            operation="SELECT",
            table="issues",
        )._value.get()

        assert new_value == initial_value + 1

    def test_cache_hits_and_misses(self):
        """Test cache hit/miss counters."""
        hits_initial = cache_hits_total.labels(cache_type="redis")._value.get()
        misses_initial = cache_misses_total.labels(cache_type="redis")._value.get()

        cache_hits_total.labels(cache_type="redis").inc()
        cache_misses_total.labels(cache_type="redis").inc()

        hits_new = cache_hits_total.labels(cache_type="redis")._value.get()
        misses_new = cache_misses_total.labels(cache_type="redis")._value.get()

        assert hits_new == hits_initial + 1
        assert misses_new == misses_initial + 1

    def test_jira_api_requests_total(self):
        """Test Jira API requests counter."""
        initial_value = jira_api_requests_total.labels(
            method="GET",
            endpoint="/rest/api/3/issue",
            status="200",
        )._value.get()

        jira_api_requests_total.labels(
            method="GET",
            endpoint="/rest/api/3/issue",
            status="200",
        ).inc()

        new_value = jira_api_requests_total.labels(
            method="GET",
            endpoint="/rest/api/3/issue",
            status="200",
        )._value.get()

        assert new_value == initial_value + 1

    def test_get_metrics(self):
        """Test getting metrics in Prometheus format."""
        metrics = get_metrics()

        assert isinstance(metrics, bytes)
        assert b"http_requests_total" in metrics
        assert b"db_queries_total" in metrics
        assert b"cache_hits_total" in metrics

