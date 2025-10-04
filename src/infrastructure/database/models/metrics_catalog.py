"""Metrics Catalog model for analytics."""

from typing import Optional, List, Dict, Any

from sqlalchemy import String, Text, Boolean, Index, UniqueConstraint, ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, UUIDMixin, TimestampMixin, TenantMixin


class MetricsCatalog(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """Metrics catalog storing predefined analytics metrics.
    
    Each metric includes:
    - SQL template for execution
    - Parameters and aggregation method
    - Semantic embedding for NL search
    - Category and tags for organization
    """
    
    __tablename__ = "metrics_catalog"
    
    # Metric Identifiers
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Unique metric name (snake_case, e.g., 'sprint_velocity')"
    )
    
    display_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Human-readable metric name (e.g., 'Sprint Velocity')"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed description of what this metric measures"
    )
    
    # Categorization
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Metric category: velocity, quality, cycle_time, predictability, etc."
    )
    
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String),
        nullable=True,
        doc="Tags for filtering and search (e.g., ['agile', 'scrum', 'team'])"
    )
    
    # SQL Configuration
    sql_template: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="SQL template with placeholders (e.g., {tenant_id}, {start_date})"
    )
    
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Parameter definitions: {name: {type, required, default, description}}"
    )
    
    aggregation: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Aggregation method: sum, avg, count, min, max, median, percentile"
    )
    
    unit: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Unit of measurement: points, days, count, percentage, etc."
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether metric is active and available for use"
    )
    
    # Semantic Search
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        ARRAY(float),
        nullable=True,
        doc="Vector embedding for semantic search (1536 dimensions for OpenAI)"
    )
    
    # Table arguments
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_metrics_catalog_tenant_name"
        ),
        Index("idx_metrics_catalog_tenant", "tenant_id"),
        Index("idx_metrics_catalog_category", "category"),
        Index("idx_metrics_catalog_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        """String representation of MetricsCatalog."""
        return (
            f"<MetricsCatalog(id={self.id}, name='{self.name}', "
            f"category='{self.category}', is_active={self.is_active})>"
        )
    
    @property
    def has_embedding(self) -> bool:
        """Check if metric has semantic embedding."""
        return self.embedding is not None and len(self.embedding) > 0
    
    @property
    def parameter_names(self) -> List[str]:
        """Get list of parameter names."""
        if not self.parameters:
            return []
        return list(self.parameters.keys())
    
    @property
    def required_parameters(self) -> List[str]:
        """Get list of required parameter names."""
        if not self.parameters:
            return []
        return [
            name for name, config in self.parameters.items()
            if config.get("required", False)
        ]
    
    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate provided parameters against metric definition.
        
        Args:
            params: Dictionary of parameter values
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.parameters:
            return True, None
        
        # Check required parameters
        for param_name in self.required_parameters:
            if param_name not in params:
                return False, f"Missing required parameter: {param_name}"
        
        # Check parameter types
        for param_name, param_value in params.items():
            if param_name not in self.parameters:
                return False, f"Unknown parameter: {param_name}"
            
            expected_type = self.parameters[param_name].get("type")
            if expected_type:
                # Basic type checking
                type_map = {
                    "string": str,
                    "integer": int,
                    "float": (int, float),
                    "boolean": bool,
                    "date": str,  # Dates come as strings
                }
                expected_python_type = type_map.get(expected_type)
                if expected_python_type and not isinstance(param_value, expected_python_type):
                    return False, f"Parameter {param_name} must be of type {expected_type}"
        
        return True, None

