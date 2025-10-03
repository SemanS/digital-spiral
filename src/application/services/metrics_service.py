"""Metrics service for tracking MCP operations."""

import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID


class MetricsCollector:
    """In-memory metrics collector for MCP operations.

    This is a simple implementation for development. In production,
    use Prometheus or similar metrics system.
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._counters: Dict[str, int] = defaultdict(int)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._gauges: Dict[str, float] = {}
        self._last_reset = datetime.now(timezone.utc)

    def increment(self, metric: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric.

        Args:
            metric: Metric name
            value: Value to increment by (default: 1)
            labels: Optional labels for the metric
        """
        key = self._make_key(metric, labels)
        self._counters[key] += value

    def observe(self, metric: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value for a histogram metric.

        Args:
            metric: Metric name
            value: Value to observe
            labels: Optional labels for the metric
        """
        key = self._make_key(metric, labels)
        self._histograms[key].append(value)

    def set_gauge(self, metric: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric.

        Args:
            metric: Metric name
            value: Value to set
            labels: Optional labels for the metric
        """
        key = self._make_key(metric, labels)
        self._gauges[key] = value

    def get_counter(self, metric: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get counter value.

        Args:
            metric: Metric name
            labels: Optional labels

        Returns:
            Counter value
        """
        key = self._make_key(metric, labels)
        return self._counters.get(key, 0)

    def get_histogram_stats(
        self, metric: str, labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Get histogram statistics.

        Args:
            metric: Metric name
            labels: Optional labels

        Returns:
            Dictionary with min, max, avg, p50, p90, p95, p99
        """
        key = self._make_key(metric, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {
                "count": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "p50": 0,
                "p90": 0,
                "p95": 0,
                "p99": 0,
            }

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": self._percentile(sorted_values, 50),
            "p90": self._percentile(sorted_values, 90),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
        }

    def get_gauge(self, metric: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value.

        Args:
            metric: Metric name
            labels: Optional labels

        Returns:
            Gauge value
        """
        key = self._make_key(metric, labels)
        return self._gauges.get(key, 0.0)

    def get_all_metrics(self) -> Dict[str, any]:
        """Get all metrics.

        Returns:
            Dictionary with all metrics
        """
        return {
            "counters": dict(self._counters),
            "histograms": {
                key: self.get_histogram_stats(key.split(":")[0])
                for key in self._histograms.keys()
            },
            "gauges": dict(self._gauges),
            "last_reset": self._last_reset.isoformat(),
        }

    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._histograms.clear()
        self._gauges.clear()
        self._last_reset = datetime.now(timezone.utc)

    @staticmethod
    def _make_key(metric: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Make a key from metric name and labels.

        Args:
            metric: Metric name
            labels: Optional labels

        Returns:
            Key string
        """
        if not labels:
            return metric

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric}:{label_str}"

    @staticmethod
    def _percentile(sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values.

        Args:
            sorted_values: Sorted list of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not sorted_values:
            return 0.0

        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]


# Global metrics collector instance
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance.

    Returns:
        MetricsCollector instance
    """
    return _metrics_collector


# Convenience functions
def increment_counter(metric: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
    """Increment a counter metric.

    Args:
        metric: Metric name
        value: Value to increment by
        labels: Optional labels
    """
    _metrics_collector.increment(metric, value, labels)


def observe_duration(metric: str, duration_ms: float, labels: Optional[Dict[str, str]] = None):
    """Observe a duration metric.

    Args:
        metric: Metric name
        duration_ms: Duration in milliseconds
        labels: Optional labels
    """
    _metrics_collector.observe(metric, duration_ms, labels)


def set_gauge(metric: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Set a gauge metric.

    Args:
        metric: Metric name
        value: Value to set
        labels: Optional labels
    """
    _metrics_collector.set_gauge(metric, value, labels)


class Timer:
    """Context manager for timing operations."""

    def __init__(self, metric: str, labels: Optional[Dict[str, str]] = None):
        """Initialize timer.

        Args:
            metric: Metric name
            labels: Optional labels
        """
        self.metric = metric
        self.labels = labels
        self.start_time = None
        self.duration_ms = None

    def __enter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record duration."""
        self.duration_ms = (time.time() - self.start_time) * 1000
        observe_duration(self.metric, self.duration_ms, self.labels)


__all__ = [
    "MetricsCollector",
    "get_metrics_collector",
    "increment_counter",
    "observe_duration",
    "set_gauge",
    "Timer",
]

