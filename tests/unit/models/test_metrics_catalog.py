"""Unit tests for MetricsCatalog model."""

import pytest
from uuid import uuid4

from src.infrastructure.database.models import MetricsCatalog


class TestMetricsCatalog:
    """Test MetricsCatalog model."""

    def test_metrics_catalog_creation(self):
        """Test creating a MetricsCatalog instance."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="sprint_velocity",
            display_name="Sprint Velocity",
            description="Average story points completed per sprint",
            category="velocity",
            sql_template="SELECT AVG(completed_points) FROM sprints WHERE tenant_id = {tenant_id}",
            aggregation="avg",
            unit="points",
            is_active=True,
        )

        assert metric.name == "sprint_velocity"
        assert metric.display_name == "Sprint Velocity"
        assert metric.category == "velocity"
        assert metric.aggregation == "avg"
        assert metric.unit == "points"
        assert metric.is_active is True

    def test_metrics_catalog_repr(self):
        """Test MetricsCatalog __repr__ method."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="sprint_velocity",
            display_name="Sprint Velocity",
            description="Test metric",
            category="velocity",
            sql_template="SELECT 1",
            aggregation="avg",
        )

        repr_str = repr(metric)
        assert "MetricsCatalog" in repr_str
        assert "sprint_velocity" in repr_str
        assert "velocity" in repr_str

    def test_has_embedding_property_false(self):
        """Test has_embedding property when no embedding."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
        )

        assert metric.has_embedding is False

    def test_has_embedding_property_true(self):
        """Test has_embedding property when embedding exists."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            embedding=[0.1, 0.2, 0.3],
        )

        assert metric.has_embedding is True

    def test_parameter_names_property_empty(self):
        """Test parameter_names property when no parameters."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
        )

        assert metric.parameter_names == []

    def test_parameter_names_property(self):
        """Test parameter_names property."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            parameters={
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True},
                "project_key": {"type": "string", "required": False},
            },
        )

        assert set(metric.parameter_names) == {"start_date", "end_date", "project_key"}

    def test_required_parameters_property(self):
        """Test required_parameters property."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            parameters={
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True},
                "project_key": {"type": "string", "required": False},
            },
        )

        assert set(metric.required_parameters) == {"start_date", "end_date"}

    def test_validate_parameters_success(self):
        """Test validate_parameters with valid parameters."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            parameters={
                "start_date": {"type": "date", "required": True},
                "limit": {"type": "integer", "required": False},
            },
        )

        is_valid, error = metric.validate_parameters({
            "start_date": "2024-01-01",
            "limit": 10,
        })

        assert is_valid is True
        assert error is None

    def test_validate_parameters_missing_required(self):
        """Test validate_parameters with missing required parameter."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            parameters={
                "start_date": {"type": "date", "required": True},
            },
        )

        is_valid, error = metric.validate_parameters({})

        assert is_valid is False
        assert "Missing required parameter: start_date" in error

    def test_validate_parameters_unknown_parameter(self):
        """Test validate_parameters with unknown parameter."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            parameters={
                "start_date": {"type": "date", "required": True},
            },
        )

        is_valid, error = metric.validate_parameters({
            "start_date": "2024-01-01",
            "unknown_param": "value",
        })

        assert is_valid is False
        assert "Unknown parameter: unknown_param" in error

    def test_validate_parameters_wrong_type(self):
        """Test validate_parameters with wrong parameter type."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            parameters={
                "limit": {"type": "integer", "required": True},
            },
        )

        is_valid, error = metric.validate_parameters({
            "limit": "not_an_integer",
        })

        assert is_valid is False
        assert "must be of type integer" in error

    def test_metrics_catalog_with_tags(self):
        """Test metrics catalog with tags."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            tags=["agile", "scrum", "velocity"],
        )

        assert metric.tags == ["agile", "scrum", "velocity"]

    def test_metrics_catalog_inactive(self):
        """Test inactive metrics catalog."""
        metric = MetricsCatalog(
            tenant_id=uuid4(),
            name="test_metric",
            display_name="Test Metric",
            description="Test",
            category="test",
            sql_template="SELECT 1",
            aggregation="count",
            is_active=False,
        )

        assert metric.is_active is False

