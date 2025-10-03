"""Prometheus metrics exporter."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from typing import Dict, Optional

from .metrics_service import MetricsCollector


class PrometheusExporter:
    """Export metrics to Prometheus format."""

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """Initialize Prometheus exporter.

        Args:
            metrics_collector: MetricsCollector instance to export from
        """
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.registry = CollectorRegistry()
        
        # Create Prometheus metrics
        self._prometheus_counters: Dict[str, Counter] = {}
        self._prometheus_histograms: Dict[str, Histogram] = {}
        self._prometheus_gauges: Dict[str, Gauge] = {}

    def export(self) -> bytes:
        """Export metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        # Get all metrics from collector
        all_metrics = self.metrics_collector.get_all_metrics()
        
        # Update Prometheus metrics
        self._update_counters(all_metrics.get("counters", {}))
        self._update_histograms(all_metrics.get("histograms", {}))
        self._update_gauges(all_metrics.get("gauges", {}))
        
        # Generate Prometheus format
        return generate_latest(self.registry)

    def _update_counters(self, counters: Dict[str, float]):
        """Update Prometheus counters."""
        for metric_name, value in counters.items():
            # Parse metric name and labels
            name, labels = self._parse_metric_name(metric_name)
            
            # Get or create counter
            if name not in self._prometheus_counters:
                self._prometheus_counters[name] = Counter(
                    name,
                    f"Counter metric: {name}",
                    labelnames=list(labels.keys()) if labels else [],
                    registry=self.registry,
                )
            
            # Set counter value
            if labels:
                self._prometheus_counters[name].labels(**labels)._value.set(value)
            else:
                self._prometheus_counters[name]._value.set(value)

    def _update_histograms(self, histograms: Dict[str, Dict]):
        """Update Prometheus histograms."""
        for metric_name, stats in histograms.items():
            # Parse metric name and labels
            name, labels = self._parse_metric_name(metric_name)
            
            # Get or create histogram
            if name not in self._prometheus_histograms:
                self._prometheus_histograms[name] = Histogram(
                    name,
                    f"Histogram metric: {name}",
                    labelnames=list(labels.keys()) if labels else [],
                    registry=self.registry,
                )
            
            # Prometheus histograms are updated via observe()
            # We can't directly set histogram values, so we skip this
            # In production, you'd observe values as they come in
            pass

    def _update_gauges(self, gauges: Dict[str, float]):
        """Update Prometheus gauges."""
        for metric_name, value in gauges.items():
            # Parse metric name and labels
            name, labels = self._parse_metric_name(metric_name)
            
            # Get or create gauge
            if name not in self._prometheus_gauges:
                self._prometheus_gauges[name] = Gauge(
                    name,
                    f"Gauge metric: {name}",
                    labelnames=list(labels.keys()) if labels else [],
                    registry=self.registry,
                )
            
            # Set gauge value
            if labels:
                self._prometheus_gauges[name].labels(**labels).set(value)
            else:
                self._prometheus_gauges[name].set(value)

    def _parse_metric_name(self, metric_name: str) -> tuple[str, Dict[str, str]]:
        """Parse metric name with labels.

        Args:
            metric_name: Metric name like "metric.name:label1=value1,label2=value2"

        Returns:
            Tuple of (name, labels_dict)
        """
        if ":" not in metric_name:
            return metric_name, {}
        
        name, labels_str = metric_name.split(":", 1)
        labels = {}
        
        for label_pair in labels_str.split(","):
            if "=" in label_pair:
                key, value = label_pair.split("=", 1)
                labels[key] = value
        
        return name, labels


# Global exporter instance
_exporter: Optional[PrometheusExporter] = None


def get_prometheus_exporter() -> PrometheusExporter:
    """Get global Prometheus exporter instance.

    Returns:
        PrometheusExporter instance
    """
    global _exporter
    if _exporter is None:
        _exporter = PrometheusExporter()
    return _exporter


def export_metrics() -> bytes:
    """Export metrics in Prometheus format.

    Returns:
        Metrics in Prometheus text format
    """
    return get_prometheus_exporter().export()


__all__ = [
    "PrometheusExporter",
    "get_prometheus_exporter",
    "export_metrics",
]

