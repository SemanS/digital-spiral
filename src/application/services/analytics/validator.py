"""AnalyticsSpec Validator for validating specs against schema and catalog."""

from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.schemas.analytics_spec import (
    AnalyticsSpec,
    FilterOperator,
    AggregationType,
)
from .metrics_catalog_service import MetricsCatalogService


class AnalyticsSpecValidator:
    """Validate AnalyticsSpec against schema and metrics catalog."""
    
    # Valid columns for each entity
    VALID_COLUMNS = {
        "issues": {
            "id", "key", "summary", "description", "issue_type", "status", "priority",
            "assignee_id", "assignee_name", "reporter_id", "reporter_name",
            "story_points", "created_at", "updated_at", "resolved_at", "in_progress_at",
            "project_id", "project_key", "project_name",
            "tenant_id", "instance_id",
        },
        "sprints": {
            "id", "sprint_id", "board_id", "name", "state", "goal",
            "start_date", "end_date", "complete_date",
            "tenant_id", "instance_id", "created_at", "updated_at",
        },
        "comments": {
            "id", "body", "author_id", "author_name",
            "created_at", "updated_at",
            "issue_id", "tenant_id", "instance_id",
        },
        "changelogs": {
            "id", "field", "from_value", "to_value",
            "created_at", "author_id", "author_name",
            "issue_id", "tenant_id", "instance_id",
        },
    }
    
    # Whitelisted operators
    WHITELISTED_OPERATORS = {op.value for op in FilterOperator}
    
    # Limits
    MAX_LIMIT_INTERACTIVE = 1000
    MAX_LIMIT_JOBS = 100000
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        """Initialize validator.
        
        Args:
            session: Database session
            tenant_id: Tenant ID
        """
        self.session = session
        self.tenant_id = tenant_id
        self.metrics_catalog = MetricsCatalogService(session)
    
    async def validate(
        self,
        spec: AnalyticsSpec,
        is_job: bool = False,
    ) -> Dict[str, Any]:
        """Validate AnalyticsSpec.
        
        Args:
            spec: AnalyticsSpec to validate
            is_job: Whether this is a background job (allows higher limits)
            
        Returns:
            Validation results with errors and warnings
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # Validate entity
        entity_errors = self._validate_entity(spec)
        errors.extend(entity_errors)
        
        # Validate metrics
        metrics_errors = await self._validate_metrics(spec)
        errors.extend(metrics_errors)
        
        # Validate filters
        filter_errors = self._validate_filters(spec)
        errors.extend(filter_errors)
        
        # Validate group_by
        group_by_errors = self._validate_group_by(spec)
        errors.extend(group_by_errors)
        
        # Validate sort_by
        sort_by_errors = self._validate_sort_by(spec)
        errors.extend(sort_by_errors)
        
        # Validate limits
        limit_errors, limit_warnings = self._validate_limits(spec, is_job)
        errors.extend(limit_errors)
        warnings.extend(limit_warnings)
        
        # Validate date range
        date_errors = self._validate_date_range(spec)
        errors.extend(date_errors)
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    def _validate_entity(self, spec: AnalyticsSpec) -> List[str]:
        """Validate entity.
        
        Args:
            spec: AnalyticsSpec
            
        Returns:
            List of errors
        """
        errors = []
        
        if spec.entity not in self.VALID_COLUMNS:
            errors.append(f"Invalid entity: {spec.entity}")
        
        return errors
    
    async def _validate_metrics(self, spec: AnalyticsSpec) -> List[str]:
        """Validate metrics.
        
        Args:
            spec: AnalyticsSpec
            
        Returns:
            List of errors
        """
        errors = []
        
        if not spec.metrics:
            errors.append("At least one metric is required")
            return errors
        
        valid_columns = self.VALID_COLUMNS.get(spec.entity, set())
        
        for metric in spec.metrics:
            # Validate field exists for aggregations that require it
            if metric.aggregation in [
                AggregationType.SUM,
                AggregationType.AVG,
                AggregationType.MIN,
                AggregationType.MAX,
                AggregationType.MEDIAN,
                AggregationType.PERCENTILE,
            ]:
                if not metric.field:
                    errors.append(
                        f"Metric '{metric.name}' with aggregation '{metric.aggregation}' "
                        f"requires a field"
                    )
                elif metric.field not in valid_columns:
                    errors.append(
                        f"Invalid field '{metric.field}' for metric '{metric.name}' "
                        f"in entity '{spec.entity}'"
                    )
        
        return errors
    
    def _validate_filters(self, spec: AnalyticsSpec) -> List[str]:
        """Validate filters.
        
        Args:
            spec: AnalyticsSpec
            
        Returns:
            List of errors
        """
        errors = []
        
        valid_columns = self.VALID_COLUMNS.get(spec.entity, set())
        
        for filter_cond in spec.filters:
            # Validate field exists
            if filter_cond.field not in valid_columns:
                errors.append(
                    f"Invalid filter field '{filter_cond.field}' "
                    f"for entity '{spec.entity}'"
                )
            
            # Validate operator is whitelisted
            if filter_cond.operator not in self.WHITELISTED_OPERATORS:
                errors.append(
                    f"Invalid filter operator '{filter_cond.operator}' "
                    f"for field '{filter_cond.field}'"
                )
        
        return errors
    
    def _validate_group_by(self, spec: AnalyticsSpec) -> List[str]:
        """Validate group_by.
        
        Args:
            spec: AnalyticsSpec
            
        Returns:
            List of errors
        """
        errors = []
        
        valid_columns = self.VALID_COLUMNS.get(spec.entity, set())
        
        for group_by in spec.group_by:
            # Validate field exists
            if group_by.field not in valid_columns:
                errors.append(
                    f"Invalid group_by field '{group_by.field}' "
                    f"for entity '{spec.entity}'"
                )
        
        return errors
    
    def _validate_sort_by(self, spec: AnalyticsSpec) -> List[str]:
        """Validate sort_by.
        
        Args:
            spec: AnalyticsSpec
            
        Returns:
            List of errors
        """
        errors = []
        
        valid_columns = self.VALID_COLUMNS.get(spec.entity, set())
        metric_names = {m.name for m in spec.metrics}
        
        for sort in spec.sort_by:
            # Field must be either a column or a metric name
            if sort.field not in valid_columns and sort.field not in metric_names:
                errors.append(
                    f"Invalid sort_by field '{sort.field}'. "
                    f"Must be a valid column or metric name"
                )
        
        return errors
    
    def _validate_limits(
        self,
        spec: AnalyticsSpec,
        is_job: bool,
    ) -> tuple[List[str], List[str]]:
        """Validate limits.
        
        Args:
            spec: AnalyticsSpec
            is_job: Whether this is a background job
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        max_limit = self.MAX_LIMIT_JOBS if is_job else self.MAX_LIMIT_INTERACTIVE
        
        if spec.limit is not None:
            if spec.limit < 1:
                errors.append("Limit must be at least 1")
            elif spec.limit > max_limit:
                errors.append(
                    f"Limit {spec.limit} exceeds maximum of {max_limit} "
                    f"for {'jobs' if is_job else 'interactive queries'}"
                )
            elif spec.limit > 100 and not is_job:
                warnings.append(
                    f"Large limit ({spec.limit}) may impact performance. "
                    f"Consider using a background job for limits > 100"
                )
        
        if spec.offset is not None and spec.offset < 0:
            errors.append("Offset must be non-negative")
        
        return errors, warnings
    
    def _validate_date_range(self, spec: AnalyticsSpec) -> List[str]:
        """Validate date range.
        
        Args:
            spec: AnalyticsSpec
            
        Returns:
            List of errors
        """
        errors = []
        
        if spec.start_date and spec.end_date:
            if spec.start_date > spec.end_date:
                errors.append("start_date must be before end_date")
        
        return errors

