"""Predefined analytics metrics catalog.

This module defines all predefined metrics that can be used in analytics queries.
Each metric includes SQL template, parameters, and metadata.
"""

from typing import Dict, Any, List
from enum import Enum


class MetricCategory(str, Enum):
    """Metric categories."""
    VELOCITY = "velocity"
    QUALITY = "quality"
    CYCLE_TIME = "cycle_time"
    PREDICTABILITY = "predictability"
    THROUGHPUT = "throughput"
    WORKLOAD = "workload"
    COLLABORATION = "collaboration"


# Predefined metrics catalog
PREDEFINED_METRICS: List[Dict[str, Any]] = [
    # ========== VELOCITY METRICS ==========
    {
        "name": "sprint_velocity",
        "display_name": "Sprint Velocity",
        "description": "Average story points completed per sprint",
        "category": MetricCategory.VELOCITY,
        "sql_template": """
            SELECT 
                AVG(completed_points) as avg_velocity,
                STDDEV(completed_points) as stddev_velocity,
                MIN(completed_points) as min_velocity,
                MAX(completed_points) as max_velocity
            FROM mv_sprint_stats_enriched
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND start_date >= :start_date
                AND end_date <= :end_date
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
        },
        "aggregation": "avg",
        "unit": "points",
        "tags": ["agile", "scrum", "velocity", "sprint"],
    },
    
    {
        "name": "velocity_trend",
        "display_name": "Velocity Trend",
        "description": "Sprint velocity over time with trend line",
        "category": MetricCategory.VELOCITY,
        "sql_template": """
            SELECT 
                sprint_name,
                start_date,
                velocity,
                velocity_z_score,
                avg_velocity as team_avg
            FROM mv_sprint_stats_enriched
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND start_date >= :start_date
                AND end_date <= :end_date
            ORDER BY start_date ASC
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
        },
        "aggregation": "none",
        "unit": "points",
        "tags": ["agile", "scrum", "velocity", "trend"],
    },
    
    # ========== CYCLE TIME METRICS ==========
    {
        "name": "avg_cycle_time",
        "display_name": "Average Cycle Time",
        "description": "Average time from in progress to done",
        "category": MetricCategory.CYCLE_TIME,
        "sql_template": """
            SELECT 
                AVG(EXTRACT(EPOCH FROM (resolved_at - in_progress_at)) / 86400) as avg_cycle_time_days,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (resolved_at - in_progress_at)) / 86400) as median_cycle_time_days,
                PERCENTILE_CONT(0.85) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (resolved_at - in_progress_at)) / 86400) as p85_cycle_time_days
            FROM issues
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND in_progress_at IS NOT NULL
                AND resolved_at IS NOT NULL
                AND created_at >= :start_date
                AND created_at <= :end_date
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
        },
        "aggregation": "avg",
        "unit": "days",
        "tags": ["cycle_time", "flow", "efficiency"],
    },
    
    {
        "name": "cycle_time_by_type",
        "display_name": "Cycle Time by Issue Type",
        "description": "Average cycle time grouped by issue type",
        "category": MetricCategory.CYCLE_TIME,
        "sql_template": """
            SELECT 
                issue_type,
                COUNT(*) as issue_count,
                AVG(EXTRACT(EPOCH FROM (resolved_at - in_progress_at)) / 86400) as avg_cycle_time_days,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (resolved_at - in_progress_at)) / 86400) as median_cycle_time_days
            FROM issues
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND in_progress_at IS NOT NULL
                AND resolved_at IS NOT NULL
                AND created_at >= :start_date
                AND created_at <= :end_date
            GROUP BY issue_type
            ORDER BY avg_cycle_time_days DESC
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
        },
        "aggregation": "avg",
        "unit": "days",
        "tags": ["cycle_time", "issue_type", "breakdown"],
    },
    
    # ========== QUALITY METRICS ==========
    {
        "name": "defect_rate",
        "display_name": "Defect Rate",
        "description": "Percentage of issues that are bugs",
        "category": MetricCategory.QUALITY,
        "sql_template": """
            SELECT 
                COUNT(*) FILTER (WHERE issue_type = 'Bug') as bug_count,
                COUNT(*) as total_count,
                (COUNT(*) FILTER (WHERE issue_type = 'Bug')::FLOAT / NULLIF(COUNT(*), 0) * 100) as defect_rate_percent
            FROM issues
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND created_at >= :start_date
                AND created_at <= :end_date
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
        },
        "aggregation": "avg",
        "unit": "percentage",
        "tags": ["quality", "bugs", "defects"],
    },
    
    {
        "name": "reopened_issues",
        "display_name": "Reopened Issues",
        "description": "Number and percentage of issues that were reopened",
        "category": MetricCategory.QUALITY,
        "sql_template": """
            SELECT 
                COUNT(DISTINCT i.id) FILTER (WHERE c.field = 'status' AND c.to_value = 'Reopened') as reopened_count,
                COUNT(DISTINCT i.id) as total_resolved,
                (COUNT(DISTINCT i.id) FILTER (WHERE c.field = 'status' AND c.to_value = 'Reopened')::FLOAT / 
                 NULLIF(COUNT(DISTINCT i.id), 0) * 100) as reopened_rate_percent
            FROM issues i
            LEFT JOIN changelogs c ON i.id = c.issue_id
            WHERE i.tenant_id = :tenant_id
                AND i.instance_id = :instance_id
                AND i.resolved_at IS NOT NULL
                AND i.created_at >= :start_date
                AND i.created_at <= :end_date
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
        },
        "aggregation": "count",
        "unit": "count",
        "tags": ["quality", "reopened", "rework"],
    },
    
    # ========== PREDICTABILITY METRICS ==========
    {
        "name": "commitment_accuracy",
        "display_name": "Sprint Commitment Accuracy",
        "description": "Percentage of committed story points that were completed",
        "category": MetricCategory.PREDICTABILITY,
        "sql_template": """
            SELECT 
                AVG(commitment_accuracy * 100) as avg_commitment_accuracy_percent,
                STDDEV(commitment_accuracy * 100) as stddev_commitment_accuracy,
                MIN(commitment_accuracy * 100) as min_commitment_accuracy,
                MAX(commitment_accuracy * 100) as max_commitment_accuracy
            FROM mv_sprint_stats_enriched
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND start_date >= :start_date
                AND end_date <= :end_date
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
        },
        "aggregation": "avg",
        "unit": "percentage",
        "tags": ["predictability", "commitment", "sprint"],
    },
    
    # ========== THROUGHPUT METRICS ==========
    {
        "name": "throughput",
        "display_name": "Throughput",
        "description": "Number of issues completed per time period",
        "category": MetricCategory.THROUGHPUT,
        "sql_template": """
            SELECT 
                DATE_TRUNC(:interval, resolved_at) as period,
                COUNT(*) as issues_completed
            FROM issues
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND resolved_at IS NOT NULL
                AND resolved_at >= :start_date
                AND resolved_at <= :end_date
            GROUP BY DATE_TRUNC(:interval, resolved_at)
            ORDER BY period ASC
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
            "start_date": {"type": "date", "required": True, "description": "Start date"},
            "end_date": {"type": "date", "required": True, "description": "End date"},
            "interval": {"type": "string", "required": False, "default": "week", "description": "Time interval (day, week, month)"},
        },
        "aggregation": "count",
        "unit": "count",
        "tags": ["throughput", "flow", "delivery"],
    },
    
    # ========== WORKLOAD METRICS ==========
    {
        "name": "workload_distribution",
        "display_name": "Workload Distribution",
        "description": "Distribution of open issues by assignee",
        "category": MetricCategory.WORKLOAD,
        "sql_template": """
            SELECT 
                assignee_id,
                assignee_name,
                COUNT(*) as open_issues,
                SUM(story_points) as total_story_points
            FROM issues
            WHERE tenant_id = :tenant_id
                AND instance_id = :instance_id
                AND status NOT IN ('Done', 'Closed', 'Resolved')
                AND assignee_id IS NOT NULL
            GROUP BY assignee_id, assignee_name
            ORDER BY open_issues DESC
            LIMIT 20
        """,
        "parameters": {
            "tenant_id": {"type": "uuid", "required": True, "description": "Tenant ID"},
            "instance_id": {"type": "uuid", "required": True, "description": "Instance ID"},
        },
        "aggregation": "count",
        "unit": "count",
        "tags": ["workload", "assignee", "capacity"],
    },
]


def get_metric_by_name(name: str) -> Dict[str, Any] | None:
    """Get metric definition by name.
    
    Args:
        name: Metric name
        
    Returns:
        Metric definition or None if not found
    """
    for metric in PREDEFINED_METRICS:
        if metric["name"] == name:
            return metric
    return None


def get_metrics_by_category(category: MetricCategory) -> List[Dict[str, Any]]:
    """Get all metrics in a category.
    
    Args:
        category: Metric category
        
    Returns:
        List of metric definitions
    """
    return [m for m in PREDEFINED_METRICS if m["category"] == category]


def get_all_metric_names() -> List[str]:
    """Get all metric names.
    
    Returns:
        List of metric names
    """
    return [m["name"] for m in PREDEFINED_METRICS]

