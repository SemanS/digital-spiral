"""SQL Query Builder for Analytics.

Converts AnalyticsSpec to SQL queries with proper escaping and validation.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.sql import Select

from src.domain.schemas.analytics_spec import (
    AnalyticsSpec,
    FilterCondition,
    FilterOperator,
    MetricDefinition,
    AggregationType,
    GroupByDefinition,
    GroupByInterval,
    SortDefinition,
)


class QueryBuilder:
    """Build SQL queries from AnalyticsSpec."""
    
    # Entity to table mapping
    ENTITY_TABLES = {
        "issues": "issues",
        "sprints": "sprints",
        "comments": "comments",
        "changelogs": "changelogs",
    }
    
    # Operator to SQL mapping
    OPERATOR_SQL = {
        FilterOperator.EQ: "=",
        FilterOperator.NE: "!=",
        FilterOperator.GT: ">",
        FilterOperator.GTE: ">=",
        FilterOperator.LT: "<",
        FilterOperator.LTE: "<=",
        FilterOperator.IN: "IN",
        FilterOperator.NOT_IN: "NOT IN",
        FilterOperator.CONTAINS: "LIKE",
        FilterOperator.STARTS_WITH: "LIKE",
        FilterOperator.ENDS_WITH: "LIKE",
        FilterOperator.IS_NULL: "IS NULL",
        FilterOperator.IS_NOT_NULL: "IS NOT NULL",
    }
    
    # Aggregation to SQL mapping
    AGGREGATION_SQL = {
        AggregationType.SUM: "SUM",
        AggregationType.AVG: "AVG",
        AggregationType.COUNT: "COUNT",
        AggregationType.MIN: "MIN",
        AggregationType.MAX: "MAX",
        AggregationType.MEDIAN: "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {field})",
        AggregationType.PERCENTILE: "PERCENTILE_CONT({percentile}/100.0) WITHIN GROUP (ORDER BY {field})",
    }
    
    # Interval to SQL mapping
    INTERVAL_SQL = {
        GroupByInterval.DAY: "day",
        GroupByInterval.WEEK: "week",
        GroupByInterval.MONTH: "month",
        GroupByInterval.QUARTER: "quarter",
        GroupByInterval.YEAR: "year",
    }
    
    def __init__(self, tenant_id: UUID):
        """Initialize query builder.
        
        Args:
            tenant_id: Tenant ID for RLS
        """
        self.tenant_id = tenant_id
        self.params: Dict[str, Any] = {"tenant_id": tenant_id}
    
    def build_query(self, spec: AnalyticsSpec) -> tuple[str, Dict[str, Any]]:
        """Build SQL query from AnalyticsSpec.
        
        Args:
            spec: Analytics specification
            
        Returns:
            Tuple of (sql_query, parameters)
        """
        # Build SELECT clause
        select_clause = self._build_select_clause(spec.metrics, spec.group_by)
        
        # Build FROM clause
        from_clause = self._build_from_clause(spec.entity)
        
        # Build WHERE clause
        where_clause = self._build_where_clause(spec.filters, spec.start_date, spec.end_date)
        
        # Build GROUP BY clause
        group_by_clause = self._build_group_by_clause(spec.group_by)
        
        # Build ORDER BY clause
        order_by_clause = self._build_order_by_clause(spec.sort_by)
        
        # Build LIMIT/OFFSET clause
        limit_clause = self._build_limit_clause(spec.limit, spec.offset)
        
        # Combine all clauses
        query_parts = [
            select_clause,
            from_clause,
            where_clause,
            group_by_clause,
            order_by_clause,
            limit_clause,
        ]
        
        sql_query = "\n".join(part for part in query_parts if part)
        
        return sql_query, self.params
    
    def _build_select_clause(
        self,
        metrics: List[MetricDefinition],
        group_by: List[GroupByDefinition],
    ) -> str:
        """Build SELECT clause.
        
        Args:
            metrics: Metrics to select
            group_by: Group by fields
            
        Returns:
            SELECT clause
        """
        select_parts = []
        
        # Add group by fields first
        for gb in group_by:
            if gb.interval:
                # Time-based grouping
                interval = self.INTERVAL_SQL[gb.interval]
                select_parts.append(
                    f"DATE_TRUNC('{interval}', {gb.field}) AS {gb.field}_grouped"
                )
            else:
                select_parts.append(gb.field)
        
        # Add metrics
        for metric in metrics:
            agg_sql = self._build_aggregation(metric)
            select_parts.append(f"{agg_sql} AS {metric.name}")
        
        return "SELECT " + ",\n       ".join(select_parts)
    
    def _build_aggregation(self, metric: MetricDefinition) -> str:
        """Build aggregation SQL.
        
        Args:
            metric: Metric definition
            
        Returns:
            Aggregation SQL
        """
        agg_type = metric.aggregation
        
        if agg_type == AggregationType.COUNT:
            return "COUNT(*)"
        
        if agg_type == AggregationType.MEDIAN:
            template = self.AGGREGATION_SQL[agg_type]
            return template.format(field=metric.field)
        
        if agg_type == AggregationType.PERCENTILE:
            template = self.AGGREGATION_SQL[agg_type]
            return template.format(
                percentile=metric.percentile,
                field=metric.field
            )
        
        # Standard aggregations (SUM, AVG, MIN, MAX)
        agg_func = self.AGGREGATION_SQL[agg_type]
        return f"{agg_func}({metric.field})"
    
    def _build_from_clause(self, entity: str) -> str:
        """Build FROM clause.
        
        Args:
            entity: Entity name
            
        Returns:
            FROM clause
        """
        table = self.ENTITY_TABLES[entity]
        return f"FROM {table}"
    
    def _build_where_clause(
        self,
        filters: List[FilterCondition],
        start_date: Optional[Any],
        end_date: Optional[Any],
    ) -> str:
        """Build WHERE clause.
        
        Args:
            filters: Filter conditions
            start_date: Start date filter
            end_date: End date filter
            
        Returns:
            WHERE clause
        """
        conditions = []
        
        # Always filter by tenant_id for RLS
        conditions.append("tenant_id = :tenant_id")
        
        # Add date range filters
        if start_date:
            param_name = f"start_date"
            conditions.append(f"created_at >= :{param_name}")
            self.params[param_name] = start_date
        
        if end_date:
            param_name = f"end_date"
            conditions.append(f"created_at <= :{param_name}")
            self.params[param_name] = end_date
        
        # Add custom filters
        for i, filter_cond in enumerate(filters):
            condition_sql = self._build_filter_condition(filter_cond, i)
            conditions.append(condition_sql)
        
        if conditions:
            return "WHERE " + "\n  AND ".join(conditions)
        
        return ""
    
    def _build_filter_condition(self, filter_cond: FilterCondition, index: int) -> str:
        """Build single filter condition.
        
        Args:
            filter_cond: Filter condition
            index: Filter index for parameter naming
            
        Returns:
            Filter condition SQL
        """
        field = filter_cond.field
        operator = filter_cond.operator
        value = filter_cond.value
        
        # Handle NULL operators
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            op_sql = self.OPERATOR_SQL[operator]
            return f"{field} {op_sql}"
        
        # Handle LIKE operators
        if operator == FilterOperator.CONTAINS:
            param_name = f"filter_{index}_value"
            self.params[param_name] = f"%{value}%"
            return f"{field} LIKE :{param_name}"
        
        if operator == FilterOperator.STARTS_WITH:
            param_name = f"filter_{index}_value"
            self.params[param_name] = f"{value}%"
            return f"{field} LIKE :{param_name}"
        
        if operator == FilterOperator.ENDS_WITH:
            param_name = f"filter_{index}_value"
            self.params[param_name] = f"%{value}"
            return f"{field} LIKE :{param_name}"
        
        # Handle IN operators
        if operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            param_name = f"filter_{index}_value"
            self.params[param_name] = tuple(value)
            op_sql = self.OPERATOR_SQL[operator]
            return f"{field} {op_sql} :{param_name}"
        
        # Standard operators
        param_name = f"filter_{index}_value"
        self.params[param_name] = value
        op_sql = self.OPERATOR_SQL[operator]
        return f"{field} {op_sql} :{param_name}"
    
    def _build_group_by_clause(self, group_by: List[GroupByDefinition]) -> str:
        """Build GROUP BY clause.
        
        Args:
            group_by: Group by definitions
            
        Returns:
            GROUP BY clause
        """
        if not group_by:
            return ""
        
        group_fields = []
        for gb in group_by:
            if gb.interval:
                interval = self.INTERVAL_SQL[gb.interval]
                group_fields.append(f"DATE_TRUNC('{interval}', {gb.field})")
            else:
                group_fields.append(gb.field)
        
        return "GROUP BY " + ", ".join(group_fields)
    
    def _build_order_by_clause(self, sort_by: List[SortDefinition]) -> str:
        """Build ORDER BY clause.
        
        Args:
            sort_by: Sort definitions
            
        Returns:
            ORDER BY clause
        """
        if not sort_by:
            return ""
        
        sort_parts = []
        for sort in sort_by:
            direction = sort.direction.upper()
            sort_parts.append(f"{sort.field} {direction}")
        
        return "ORDER BY " + ", ".join(sort_parts)
    
    def _build_limit_clause(self, limit: Optional[int], offset: Optional[int]) -> str:
        """Build LIMIT/OFFSET clause.
        
        Args:
            limit: Limit value
            offset: Offset value
            
        Returns:
            LIMIT/OFFSET clause
        """
        parts = []
        
        if limit:
            parts.append(f"LIMIT {limit}")
        
        if offset:
            parts.append(f"OFFSET {offset}")
        
        return " ".join(parts) if parts else ""

