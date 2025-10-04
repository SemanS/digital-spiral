"""Analytics Specification schema for query definition."""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class AggregationType(str, Enum):
    """Aggregation types for metrics."""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    PERCENTILE = "percentile"


class FilterOperator(str, Enum):
    """Filter operators."""
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list
    CONTAINS = "contains"  # String contains
    STARTS_WITH = "starts_with"  # String starts with
    ENDS_WITH = "ends_with"  # String ends with
    IS_NULL = "is_null"  # Is null
    IS_NOT_NULL = "is_not_null"  # Is not null


class GroupByInterval(str, Enum):
    """Time interval for grouping."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class FilterCondition(BaseModel):
    """Filter condition for analytics query."""
    
    field: str = Field(
        ...,
        description="Field name to filter on (e.g., 'status', 'priority', 'created_at')"
    )
    
    operator: FilterOperator = Field(
        ...,
        description="Filter operator"
    )
    
    value: Any = Field(
        ...,
        description="Filter value (type depends on field and operator)"
    )
    
    @field_validator('value')
    @classmethod
    def validate_value_for_operator(cls, v, info):
        """Validate value matches operator requirements."""
        operator = info.data.get('operator')
        
        if operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            if not isinstance(v, list):
                raise ValueError(f"Value must be a list for operator {operator}")
        
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            if v is not None:
                raise ValueError(f"Value must be None for operator {operator}")
        
        return v


class MetricDefinition(BaseModel):
    """Metric definition for analytics query."""
    
    name: str = Field(
        ...,
        description="Metric name (e.g., 'velocity', 'cycle_time', 'lead_time')"
    )
    
    aggregation: AggregationType = Field(
        ...,
        description="Aggregation type"
    )
    
    field: Optional[str] = Field(
        None,
        description="Field to aggregate (required for sum, avg, min, max)"
    )
    
    percentile: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Percentile value (0-100) for percentile aggregation"
    )
    
    @model_validator(mode='after')
    def validate_metric(self):
        """Validate metric definition."""
        # Field is required for certain aggregations
        if self.aggregation in [
            AggregationType.SUM,
            AggregationType.AVG,
            AggregationType.MIN,
            AggregationType.MAX,
            AggregationType.MEDIAN,
        ]:
            if not self.field:
                raise ValueError(
                    f"Field is required for aggregation type {self.aggregation}"
                )
        
        # Percentile is required for percentile aggregation
        if self.aggregation == AggregationType.PERCENTILE:
            if self.percentile is None:
                raise ValueError("Percentile value is required for percentile aggregation")
        
        return self


class GroupByDefinition(BaseModel):
    """Group by definition for analytics query."""
    
    field: str = Field(
        ...,
        description="Field to group by (e.g., 'status', 'assignee', 'sprint')"
    )
    
    interval: Optional[GroupByInterval] = Field(
        None,
        description="Time interval for date fields"
    )
    
    limit: Optional[int] = Field(
        None,
        ge=1,
        le=1000,
        description="Limit number of groups (default: no limit)"
    )


class SortDefinition(BaseModel):
    """Sort definition for analytics query."""
    
    field: str = Field(
        ...,
        description="Field to sort by"
    )
    
    direction: Literal["asc", "desc"] = Field(
        "desc",
        description="Sort direction"
    )


class AnalyticsSpec(BaseModel):
    """Analytics specification for defining queries.
    
    This is the core schema that defines what data to retrieve and how to aggregate it.
    Can be generated from natural language or provided directly.
    """
    
    # Data Source
    entity: Literal["issues", "sprints", "comments", "changelogs"] = Field(
        ...,
        description="Primary entity to query"
    )
    
    # Metrics
    metrics: List[MetricDefinition] = Field(
        ...,
        min_length=1,
        description="Metrics to calculate"
    )
    
    # Filters
    filters: List[FilterCondition] = Field(
        default_factory=list,
        description="Filter conditions (AND logic)"
    )
    
    # Grouping
    group_by: List[GroupByDefinition] = Field(
        default_factory=list,
        description="Group by fields"
    )
    
    # Sorting
    sort_by: List[SortDefinition] = Field(
        default_factory=list,
        description="Sort order"
    )
    
    # Time Range
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for time-based filtering"
    )
    
    end_date: Optional[datetime] = Field(
        None,
        description="End date for time-based filtering"
    )
    
    # Pagination
    limit: Optional[int] = Field(
        None,
        ge=1,
        le=10000,
        description="Maximum number of results"
    )
    
    offset: Optional[int] = Field(
        None,
        ge=0,
        description="Number of results to skip"
    )
    
    # Metadata
    description: Optional[str] = Field(
        None,
        description="Human-readable description of the query"
    )
    
    @model_validator(mode='after')
    def validate_spec(self):
        """Validate analytics spec."""
        # Validate date range
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")
        
        # Validate metric names are unique
        metric_names = [m.name for m in self.metrics]
        if len(metric_names) != len(set(metric_names)):
            raise ValueError("Metric names must be unique")
        
        # Validate group_by fields are unique
        group_by_fields = [g.field for g in self.group_by]
        if len(group_by_fields) != len(set(group_by_fields)):
            raise ValueError("Group by fields must be unique")
        
        return self
    
    def to_cache_key(self) -> Dict[str, Any]:
        """Convert spec to cache key dictionary.
        
        Returns:
            Dictionary suitable for hashing
        """
        return {
            "entity": self.entity,
            "metrics": [m.model_dump() for m in self.metrics],
            "filters": [f.model_dump() for f in self.filters],
            "group_by": [g.model_dump() for g in self.group_by],
            "sort_by": [s.model_dump() for s in self.sort_by],
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "limit": self.limit,
            "offset": self.offset,
        }
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "entity": "sprints",
                "metrics": [
                    {
                        "name": "avg_velocity",
                        "aggregation": "avg",
                        "field": "velocity"
                    }
                ],
                "filters": [
                    {
                        "field": "state",
                        "operator": "eq",
                        "value": "closed"
                    }
                ],
                "group_by": [
                    {
                        "field": "created_at",
                        "interval": "month"
                    }
                ],
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "limit": 100
            }
        }

