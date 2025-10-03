"""Unit tests for MetricsService."""

import pytest
import time

from src.application.services.metrics_service import (
    MetricsCollector,
    Timer,
    increment_counter,
    observe_duration,
    set_gauge,
)


@pytest.fixture
def collector():
    """Create a fresh metrics collector."""
    collector = MetricsCollector()
    collector.reset()
    return collector


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_increment_counter(self, collector):
        """Test incrementing a counter."""
        collector.increment("test.counter")
        assert collector.get_counter("test.counter") == 1

        collector.increment("test.counter", value=5)
        assert collector.get_counter("test.counter") == 6

    def test_increment_counter_with_labels(self, collector):
        """Test incrementing counters with labels."""
        collector.increment("test.counter", labels={"method": "GET"})
        collector.increment("test.counter", labels={"method": "POST"})
        collector.increment("test.counter", labels={"method": "GET"})

        assert collector.get_counter("test.counter", labels={"method": "GET"}) == 2
        assert collector.get_counter("test.counter", labels={"method": "POST"}) == 1

    def test_observe_histogram(self, collector):
        """Test observing histogram values."""
        collector.observe("test.duration", 100.0)
        collector.observe("test.duration", 200.0)
        collector.observe("test.duration", 150.0)

        stats = collector.get_histogram_stats("test.duration")
        assert stats["count"] == 3
        assert stats["min"] == 100.0
        assert stats["max"] == 200.0
        assert stats["avg"] == 150.0

    def test_histogram_percentiles(self, collector):
        """Test histogram percentile calculations."""
        # Add 100 values from 1 to 100
        for i in range(1, 101):
            collector.observe("test.duration", float(i))

        stats = collector.get_histogram_stats("test.duration")
        assert stats["count"] == 100
        assert stats["p50"] == 50.0
        assert stats["p90"] == 90.0
        assert stats["p95"] == 95.0
        assert stats["p99"] == 99.0

    def test_set_gauge(self, collector):
        """Test setting gauge values."""
        collector.set_gauge("test.gauge", 42.5)
        assert collector.get_gauge("test.gauge") == 42.5

        collector.set_gauge("test.gauge", 100.0)
        assert collector.get_gauge("test.gauge") == 100.0

    def test_gauge_with_labels(self, collector):
        """Test gauges with labels."""
        collector.set_gauge("test.gauge", 10.0, labels={"instance": "1"})
        collector.set_gauge("test.gauge", 20.0, labels={"instance": "2"})

        assert collector.get_gauge("test.gauge", labels={"instance": "1"}) == 10.0
        assert collector.get_gauge("test.gauge", labels={"instance": "2"}) == 20.0

    def test_get_all_metrics(self, collector):
        """Test getting all metrics."""
        collector.increment("counter1")
        collector.increment("counter2", value=5)
        collector.observe("histogram1", 100.0)
        collector.set_gauge("gauge1", 42.0)

        all_metrics = collector.get_all_metrics()

        assert "counters" in all_metrics
        assert "histograms" in all_metrics
        assert "gauges" in all_metrics
        assert "last_reset" in all_metrics

        assert all_metrics["counters"]["counter1"] == 1
        assert all_metrics["counters"]["counter2"] == 5
        assert all_metrics["gauges"]["gauge1"] == 42.0

    def test_reset(self, collector):
        """Test resetting metrics."""
        collector.increment("test.counter")
        collector.observe("test.duration", 100.0)
        collector.set_gauge("test.gauge", 42.0)

        collector.reset()

        assert collector.get_counter("test.counter") == 0
        assert collector.get_histogram_stats("test.duration")["count"] == 0
        assert collector.get_gauge("test.gauge") == 0.0

    def test_empty_histogram_stats(self, collector):
        """Test histogram stats for empty histogram."""
        stats = collector.get_histogram_stats("nonexistent")

        assert stats["count"] == 0
        assert stats["min"] == 0
        assert stats["max"] == 0
        assert stats["avg"] == 0
        assert stats["p50"] == 0


class TestTimer:
    """Tests for Timer context manager."""

    def test_timer_measures_duration(self, collector):
        """Test that timer measures duration."""
        with Timer("test.operation"):
            time.sleep(0.01)  # Sleep for 10ms

        stats = collector.get_histogram_stats("test.operation")
        assert stats["count"] == 1
        assert stats["min"] >= 10.0  # At least 10ms
        assert stats["min"] < 100.0  # But not too much more

    def test_timer_with_labels(self, collector):
        """Test timer with labels."""
        with Timer("test.operation", labels={"method": "GET"}):
            time.sleep(0.01)

        with Timer("test.operation", labels={"method": "POST"}):
            time.sleep(0.02)

        stats_get = collector.get_histogram_stats(
            "test.operation", labels={"method": "GET"}
        )
        stats_post = collector.get_histogram_stats(
            "test.operation", labels={"method": "POST"}
        )

        assert stats_get["count"] == 1
        assert stats_post["count"] == 1
        assert stats_post["min"] > stats_get["min"]  # POST took longer

    def test_timer_duration_attribute(self, collector):
        """Test that timer stores duration in attribute."""
        with Timer("test.operation") as timer:
            time.sleep(0.01)

        assert timer.duration_ms is not None
        assert timer.duration_ms >= 10.0


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_increment_counter_function(self, collector):
        """Test increment_counter convenience function."""
        increment_counter("test.counter")
        increment_counter("test.counter", value=5)

        assert collector.get_counter("test.counter") == 6

    def test_observe_duration_function(self, collector):
        """Test observe_duration convenience function."""
        observe_duration("test.duration", 100.0)
        observe_duration("test.duration", 200.0)

        stats = collector.get_histogram_stats("test.duration")
        assert stats["count"] == 2
        assert stats["avg"] == 150.0

    def test_set_gauge_function(self, collector):
        """Test set_gauge convenience function."""
        set_gauge("test.gauge", 42.0)

        assert collector.get_gauge("test.gauge") == 42.0

