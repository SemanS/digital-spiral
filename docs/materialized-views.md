# Materialized Views

This document describes the materialized views used in Digital Spiral for analytics and reporting.

## Overview

Materialized views are pre-computed query results stored as physical tables. They provide fast access to complex aggregations and analytics without the overhead of computing them on every request.

## Available Materialized Views

### 1. mv_issue_stats_by_project

**Purpose:** Aggregate statistics for issues grouped by project.

**Columns:**
- `tenant_id` - Tenant identifier
- `instance_id` - Jira instance identifier
- `project_id` - Project identifier
- `project_key` - Project key (e.g., "PROJ")
- `project_name` - Project name
- `total_issues` - Total number of issues
- `todo_count` - Issues in "To Do" status category
- `in_progress_count` - Issues in "In Progress" status category
- `done_count` - Issues in "Done" status category
- `bug_count` - Number of bugs
- `story_count` - Number of stories
- `task_count` - Number of tasks
- `epic_count` - Number of epics
- `highest_priority_count` - Highest priority issues
- `high_priority_count` - High priority issues
- `medium_priority_count` - Medium priority issues
- `low_priority_count` - Low priority issues
- `lowest_priority_count` - Lowest priority issues
- `unassigned_count` - Unassigned issues
- `subtask_count` - Number of subtasks
- `avg_resolution_days` - Average days to resolve issues
- `last_updated_at` - Last update timestamp
- `refreshed_at` - When the view was last refreshed

**Example Query:**
```sql
SELECT 
    project_key,
    project_name,
    total_issues,
    done_count,
    ROUND((done_count::numeric / total_issues * 100), 2) AS completion_percentage,
    avg_resolution_days
FROM mv_issue_stats_by_project
WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY total_issues DESC;
```

### 2. mv_issue_stats_by_assignee

**Purpose:** Aggregate statistics for issues grouped by assignee.

**Columns:**
- `tenant_id` - Tenant identifier
- `instance_id` - Jira instance identifier
- `assignee_account_id` - Assignee Jira account ID
- `assignee_name` - Assignee display name
- `assignee_email` - Assignee email address
- `total_assigned` - Total issues assigned
- `todo_count` - Issues in "To Do" status
- `in_progress_count` - Issues in "In Progress" status
- `done_count` - Issues in "Done" status
- `bug_count` - Number of bugs assigned
- `high_priority_count` - High/Highest priority issues
- `avg_resolution_days` - Average days to resolve
- `last_updated_at` - Last update timestamp
- `refreshed_at` - When the view was last refreshed

**Example Query:**
```sql
SELECT 
    assignee_name,
    total_assigned,
    in_progress_count,
    done_count,
    high_priority_count,
    ROUND(avg_resolution_days, 2) AS avg_days
FROM mv_issue_stats_by_assignee
WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY total_assigned DESC
LIMIT 10;
```

### 3. mv_issue_activity_timeline

**Purpose:** Daily issue creation and resolution statistics.

**Columns:**
- `tenant_id` - Tenant identifier
- `instance_id` - Jira instance identifier
- `project_id` - Project identifier
- `activity_date` - Date of activity
- `issues_created` - Issues created on this date
- `issues_resolved_same_day` - Issues created and resolved on same day
- `bugs_created` - Bugs created on this date
- `stories_created` - Stories created on this date
- `refreshed_at` - When the view was last refreshed

**Example Query:**
```sql
-- Get last 30 days of activity
SELECT 
    activity_date,
    SUM(issues_created) AS total_created,
    SUM(bugs_created) AS bugs,
    SUM(stories_created) AS stories
FROM mv_issue_activity_timeline
WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'
  AND activity_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY activity_date
ORDER BY activity_date DESC;
```

### 4. mv_issue_label_stats

**Purpose:** Statistics for issue labels.

**Columns:**
- `tenant_id` - Tenant identifier
- `instance_id` - Jira instance identifier
- `project_id` - Project identifier
- `label` - Label name
- `issue_count` - Total issues with this label
- `done_count` - Completed issues with this label
- `active_count` - Active (To Do/In Progress) issues with this label
- `refreshed_at` - When the view was last refreshed

**Example Query:**
```sql
-- Top 10 most used labels
SELECT 
    label,
    issue_count,
    done_count,
    active_count,
    ROUND((done_count::numeric / issue_count * 100), 2) AS completion_percentage
FROM mv_issue_label_stats
WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY issue_count DESC
LIMIT 10;
```

### 5. mv_comment_activity_stats

**Purpose:** Comment activity statistics per issue.

**Columns:**
- `tenant_id` - Tenant identifier
- `instance_id` - Jira instance identifier
- `issue_id` - Issue identifier
- `issue_key` - Issue key
- `project_id` - Project identifier
- `total_comments` - Total number of comments
- `unique_commenters` - Number of unique commenters
- `first_comment_at` - Timestamp of first comment
- `last_comment_at` - Timestamp of last comment
- `avg_comment_length` - Average comment length in characters
- `refreshed_at` - When the view was last refreshed

**Example Query:**
```sql
-- Most discussed issues
SELECT 
    issue_key,
    total_comments,
    unique_commenters,
    ROUND(avg_comment_length, 0) AS avg_length
FROM mv_comment_activity_stats
WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY total_comments DESC
LIMIT 10;
```

### 6. mv_changelog_activity_stats

**Purpose:** Change history statistics per issue.

**Columns:**
- `tenant_id` - Tenant identifier
- `instance_id` - Jira instance identifier
- `issue_id` - Issue identifier
- `issue_key` - Issue key
- `project_id` - Project identifier
- `total_changes` - Total number of changes
- `unique_changers` - Number of unique users who made changes
- `first_change_at` - Timestamp of first change
- `last_change_at` - Timestamp of last change
- `status_changes` - Number of status changes
- `refreshed_at` - When the view was last refreshed

**Example Query:**
```sql
-- Issues with most changes
SELECT 
    issue_key,
    total_changes,
    status_changes,
    unique_changers
FROM mv_changelog_activity_stats
WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY total_changes DESC
LIMIT 10;
```

## Refreshing Materialized Views

### Manual Refresh

Refresh a single view:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_issue_stats_by_project;
```

Refresh all views:
```sql
SELECT refresh_all_materialized_views();
```

### Automatic Refresh

Set up a cron job or scheduled task to refresh views periodically:

**Using pg_cron (PostgreSQL extension):**
```sql
-- Install pg_cron extension
CREATE EXTENSION pg_cron;

-- Schedule refresh every hour
SELECT cron.schedule(
    'refresh-materialized-views',
    '0 * * * *',  -- Every hour
    'SELECT refresh_all_materialized_views()'
);
```

**Using Python/Celery:**
```python
from celery import Celery
from sqlalchemy import text

app = Celery('tasks')

@app.task
def refresh_materialized_views():
    """Refresh all materialized views."""
    with engine.connect() as conn:
        conn.execute(text("SELECT refresh_all_materialized_views()"))
        conn.commit()

# Schedule to run every hour
app.conf.beat_schedule = {
    'refresh-views': {
        'task': 'tasks.refresh_materialized_views',
        'schedule': 3600.0,  # Every hour
    },
}
```

## Performance Considerations

### 1. Refresh Strategy

**CONCURRENT vs. Non-CONCURRENT:**
- `REFRESH MATERIALIZED VIEW CONCURRENTLY` - Allows queries during refresh but requires unique index
- `REFRESH MATERIALIZED VIEW` - Locks the view during refresh but is faster

**Recommendation:** Use CONCURRENT refresh for production to avoid blocking queries.

### 2. Refresh Frequency

Choose refresh frequency based on:
- Data freshness requirements
- View complexity
- Data volume
- Query load

**Recommendations:**
- **Real-time dashboards:** Every 5-15 minutes
- **Daily reports:** Once per day
- **Historical analytics:** Once per week

### 3. Incremental Refresh

For large datasets, consider incremental refresh patterns:

```sql
-- Example: Only refresh recent data
CREATE MATERIALIZED VIEW mv_recent_issues AS
SELECT *
FROM issues
WHERE jira_updated_at >= CURRENT_DATE - INTERVAL '7 days';
```

## Monitoring

### Check View Freshness

```sql
SELECT 
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) AS size,
    last_refresh
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY matviewname;
```

### Check Refresh Duration

```sql
-- Enable timing
\timing on

-- Refresh and measure
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_issue_stats_by_project;
```

### Monitor View Usage

```sql
SELECT 
    schemaname,
    matviewname,
    idx_scan,
    seq_scan,
    idx_tup_fetch,
    seq_tup_read
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND relname LIKE 'mv_%'
ORDER BY seq_scan + idx_scan DESC;
```

## Application Integration

### Using with SQLAlchemy

```python
from sqlalchemy import Table, MetaData, select

metadata = MetaData()

# Define materialized view as a table
issue_stats = Table(
    'mv_issue_stats_by_project',
    metadata,
    autoload_with=engine
)

# Query the view
stmt = select(issue_stats).where(
    issue_stats.c.tenant_id == tenant_id
).order_by(
    issue_stats.c.total_issues.desc()
)

results = session.execute(stmt).fetchall()
```

### Using with Repository Pattern

```python
from sqlalchemy import text

class AnalyticsRepository:
    """Repository for analytics queries."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_project_stats(self, tenant_id: UUID) -> list[dict]:
        """Get project statistics."""
        stmt = text("""
            SELECT *
            FROM mv_issue_stats_by_project
            WHERE tenant_id = :tenant_id
            ORDER BY total_issues DESC
        """)
        
        result = self.session.execute(stmt, {"tenant_id": str(tenant_id)})
        return [dict(row) for row in result]
    
    def get_assignee_stats(self, tenant_id: UUID) -> list[dict]:
        """Get assignee statistics."""
        stmt = text("""
            SELECT *
            FROM mv_issue_stats_by_assignee
            WHERE tenant_id = :tenant_id
            ORDER BY total_assigned DESC
        """)
        
        result = self.session.execute(stmt, {"tenant_id": str(tenant_id)})
        return [dict(row) for row in result]
    
    def refresh_views(self):
        """Refresh all materialized views."""
        self.session.execute(text("SELECT refresh_all_materialized_views()"))
        self.session.commit()
```

### FastAPI Endpoint Example

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/analytics/projects")
async def get_project_analytics(
    tenant_id: UUID = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Get project analytics."""
    analytics_repo = AnalyticsRepository(db)
    stats = analytics_repo.get_project_stats(tenant_id)
    return {"data": stats}

@router.post("/analytics/refresh")
async def refresh_analytics(
    db: Session = Depends(get_db)
):
    """Manually refresh materialized views."""
    analytics_repo = AnalyticsRepository(db)
    analytics_repo.refresh_views()
    return {"message": "Views refreshed successfully"}
```

## Best Practices

1. ✅ **Create unique indexes** on materialized views for CONCURRENT refresh
2. ✅ **Schedule regular refreshes** based on data freshness requirements
3. ✅ **Monitor view size** and refresh duration
4. ✅ **Use CONCURRENTLY** for production refreshes
5. ✅ **Add tenant_id filters** to all queries for multi-tenant isolation
6. ✅ **Document refresh schedules** and dependencies
7. ❌ **Don't refresh too frequently** - balance freshness vs. performance
8. ❌ **Don't create views for rarely-used queries** - use regular queries instead

## Troubleshooting

### Issue: CONCURRENT refresh fails

**Cause:** Missing unique index

**Solution:**
```sql
-- Create unique index
CREATE UNIQUE INDEX ix_mv_name_pk ON mv_name (tenant_id, id);

-- Then refresh
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_name;
```

### Issue: Refresh takes too long

**Cause:** Large dataset or complex aggregations

**Solutions:**
1. Add indexes on base tables
2. Partition base tables
3. Use incremental refresh
4. Refresh during off-peak hours

### Issue: Stale data in views

**Cause:** Infrequent refresh schedule

**Solution:** Increase refresh frequency or implement event-driven refresh:
```python
# Refresh after bulk data import
def import_issues(issues: list[Issue]):
    # Import issues
    bulk_insert_issues(issues)
    
    # Refresh views
    refresh_materialized_views()
```

