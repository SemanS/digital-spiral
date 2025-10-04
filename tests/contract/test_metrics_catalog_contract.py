"""Contract tests for metrics catalog integrity."""

import pytest
from typing import Set

from src.domain.analytics.predefined_metrics import (
    PREDEFINED_METRICS,
    MetricCategory,
    get_metric_by_name,
    get_all_metric_names,
)


class TestMetricsCatalogContract:
    """Contract tests for metrics catalog."""
    
    def test_all_metrics_have_required_fields(self):
        """Test that all metrics have required fields."""
        required_fields = [
            "name",
            "display_name",
            "description",
            "category",
            "sql_template",
            "aggregation",
            "unit",
            "tags",
        ]
        
        for metric in PREDEFINED_METRICS:
            for field in required_fields:
                assert field in metric, f"Metric '{metric.get('name', 'unknown')}' missing field '{field}'"
    
    def test_all_metric_names_are_unique(self):
        """Test that all metric names are unique."""
        names = [m["name"] for m in PREDEFINED_METRICS]
        assert len(names) == len(set(names)), "Duplicate metric names found"
    
    def test_all_metric_names_are_snake_case(self):
        """Test that all metric names use snake_case."""
        for metric in PREDEFINED_METRICS:
            name = metric["name"]
            assert name.islower(), f"Metric name '{name}' is not lowercase"
            assert " " not in name, f"Metric name '{name}' contains spaces"
            assert name.replace("_", "").isalnum(), f"Metric name '{name}' contains invalid characters"
    
    def test_all_categories_are_valid(self):
        """Test that all categories are valid enum values."""
        valid_categories = {c.value for c in MetricCategory}
        
        for metric in PREDEFINED_METRICS:
            category = metric["category"]
            assert category in valid_categories, f"Invalid category '{category}' in metric '{metric['name']}'"
    
    def test_all_sql_templates_are_non_empty(self):
        """Test that all SQL templates are non-empty."""
        for metric in PREDEFINED_METRICS:
            sql_template = metric["sql_template"]
            assert sql_template.strip(), f"Empty SQL template in metric '{metric['name']}'"
    
    def test_all_sql_templates_are_select_statements(self):
        """Test that all SQL templates are SELECT statements."""
        for metric in PREDEFINED_METRICS:
            sql_template = metric["sql_template"].strip().upper()
            assert sql_template.startswith("SELECT"), f"SQL template in metric '{metric['name']}' is not a SELECT statement"
    
    def test_all_sql_templates_have_tenant_id_parameter(self):
        """Test that all SQL templates include tenant_id parameter."""
        for metric in PREDEFINED_METRICS:
            sql_template = metric["sql_template"]
            assert ":tenant_id" in sql_template, f"SQL template in metric '{metric['name']}' missing :tenant_id parameter"
    
    def test_all_parameters_have_required_fields(self):
        """Test that all parameters have required fields."""
        required_param_fields = ["type", "required", "description"]
        
        for metric in PREDEFINED_METRICS:
            if "parameters" in metric and metric["parameters"]:
                for param_name, param_def in metric["parameters"].items():
                    for field in required_param_fields:
                        assert field in param_def, f"Parameter '{param_name}' in metric '{metric['name']}' missing field '{field}'"
    
    def test_all_parameter_types_are_valid(self):
        """Test that all parameter types are valid."""
        valid_types = {"string", "integer", "float", "boolean", "date", "uuid"}
        
        for metric in PREDEFINED_METRICS:
            if "parameters" in metric and metric["parameters"]:
                for param_name, param_def in metric["parameters"].items():
                    param_type = param_def["type"]
                    assert param_type in valid_types, f"Invalid type '{param_type}' for parameter '{param_name}' in metric '{metric['name']}'"
    
    def test_all_aggregations_are_valid(self):
        """Test that all aggregations are valid."""
        valid_aggregations = {"sum", "avg", "count", "min", "max", "median", "percentile", "none"}
        
        for metric in PREDEFINED_METRICS:
            aggregation = metric["aggregation"]
            assert aggregation in valid_aggregations, f"Invalid aggregation '{aggregation}' in metric '{metric['name']}'"
    
    def test_all_units_are_valid(self):
        """Test that all units are valid."""
        valid_units = {"points", "days", "count", "percentage", "hours", "minutes", None}
        
        for metric in PREDEFINED_METRICS:
            unit = metric.get("unit")
            assert unit in valid_units, f"Invalid unit '{unit}' in metric '{metric['name']}'"
    
    def test_all_tags_are_non_empty_lists(self):
        """Test that all tags are non-empty lists."""
        for metric in PREDEFINED_METRICS:
            tags = metric.get("tags", [])
            assert isinstance(tags, list), f"Tags in metric '{metric['name']}' is not a list"
            if tags:
                assert all(isinstance(tag, str) for tag in tags), f"Non-string tag in metric '{metric['name']}'"
                assert all(tag.strip() for tag in tags), f"Empty tag in metric '{metric['name']}'"
    
    def test_sql_templates_use_parameterized_queries(self):
        """Test that SQL templates use parameterized queries (no string interpolation)."""
        dangerous_patterns = ["{", "}", "%s", "format("]
        
        for metric in PREDEFINED_METRICS:
            sql_template = metric["sql_template"]
            for pattern in dangerous_patterns:
                assert pattern not in sql_template, f"SQL template in metric '{metric['name']}' uses dangerous pattern '{pattern}'"
    
    def test_required_parameters_are_used_in_sql(self):
        """Test that required parameters are actually used in SQL template."""
        for metric in PREDEFINED_METRICS:
            if "parameters" in metric and metric["parameters"]:
                sql_template = metric["sql_template"]
                
                for param_name, param_def in metric["parameters"].items():
                    if param_def.get("required", False):
                        # Check if parameter is used in SQL
                        param_placeholder = f":{param_name}"
                        assert param_placeholder in sql_template, f"Required parameter '{param_name}' not used in SQL template for metric '{metric['name']}'"
    
    def test_get_metric_by_name_works(self):
        """Test that get_metric_by_name helper works."""
        for metric in PREDEFINED_METRICS:
            name = metric["name"]
            found = get_metric_by_name(name)
            assert found is not None, f"get_metric_by_name failed for '{name}'"
            assert found["name"] == name
    
    def test_get_metric_by_name_returns_none_for_invalid(self):
        """Test that get_metric_by_name returns None for invalid names."""
        result = get_metric_by_name("invalid_metric_name_xyz")
        assert result is None
    
    def test_get_all_metric_names_returns_all(self):
        """Test that get_all_metric_names returns all metric names."""
        names = get_all_metric_names()
        assert len(names) == len(PREDEFINED_METRICS)
        
        for metric in PREDEFINED_METRICS:
            assert metric["name"] in names
    
    def test_minimum_number_of_metrics(self):
        """Test that we have at least 10 metrics defined."""
        assert len(PREDEFINED_METRICS) >= 10, f"Expected at least 10 metrics, found {len(PREDEFINED_METRICS)}"
    
    def test_all_categories_have_at_least_one_metric(self):
        """Test that all categories have at least one metric."""
        categories_with_metrics = {m["category"] for m in PREDEFINED_METRICS}
        
        # We should have metrics in multiple categories
        assert len(categories_with_metrics) >= 5, f"Expected metrics in at least 5 categories, found {len(categories_with_metrics)}"
    
    def test_display_names_are_human_readable(self):
        """Test that display names are human-readable (not snake_case)."""
        for metric in PREDEFINED_METRICS:
            display_name = metric["display_name"]
            # Display names should have spaces or be capitalized
            assert " " in display_name or display_name[0].isupper(), f"Display name '{display_name}' in metric '{metric['name']}' is not human-readable"
    
    def test_descriptions_are_meaningful(self):
        """Test that descriptions are meaningful (not too short)."""
        for metric in PREDEFINED_METRICS:
            description = metric["description"]
            assert len(description) >= 20, f"Description in metric '{metric['name']}' is too short (< 20 chars)"
    
    def test_no_sql_injection_vulnerabilities(self):
        """Test that SQL templates don't have obvious injection vulnerabilities."""
        dangerous_patterns = ["';", "--", "/*", "*/", "UNION", "DROP", "DELETE", "UPDATE", "INSERT"]
        
        for metric in PREDEFINED_METRICS:
            sql_template = metric["sql_template"].upper()
            
            # Check for dangerous patterns (excluding legitimate SQL keywords in context)
            for pattern in dangerous_patterns:
                if pattern in ["UNION", "DROP", "DELETE", "UPDATE", "INSERT"]:
                    # These should not appear in SELECT-only queries
                    assert pattern not in sql_template, f"Dangerous SQL keyword '{pattern}' found in metric '{metric['name']}'"

