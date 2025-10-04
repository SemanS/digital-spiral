# Analytics Engine Documentation

## Overview

The Analytics Engine is a comprehensive system for executing analytics queries on Jira/project management data. It supports both structured queries (AnalyticsSpec) and natural language queries (via LLM translation).

## Architecture

### Components

1. **Database Layer**
   - 5 tables: `sprints`, `sprint_issues`, `metrics_catalog`, `analytics_jobs`, `analytics_cache`
   - 2 materialized views: `mv_sprint_stats_enriched`, `mv_issue_comment_stats`
   - RLS policies for tenant isolation

2. **Analytics Engine**
   - `QueryBuilder` - Converts AnalyticsSpec to SQL
   - `AnalyticsExecutor` - Executes SQL queries
   - `CacheService` - Manages query result caching
   - `MetricsCatalogService` - CRUD for predefined metrics
   - `AnalyticsService` - Main orchestrator

3. **LLM Integration**
   - `NLTranslator` - Translates natural language to AnalyticsSpec
   - `PromptTemplates` - Prompt engineering for LLM
   - OpenAI GPT-4 integration

4. **API Layer**
   - 9 REST endpoints for analytics operations
   - Request validation
   - Error handling

## Quick Start

### 1. Execute a Simple Query

```python
from src.application.services.analytics import AnalyticsService
from src.domain.schemas.analytics_spec import AnalyticsSpec, MetricDefinition, AggregationType

# Create service
service = AnalyticsService(session, tenant_id)

# Define query
spec = AnalyticsSpec(
    entity="issues",
    metrics=[
        MetricDefinition(
            name="total_issues",
            aggregation=AggregationType.COUNT,
        )
    ],
)

# Execute
result = await service.execute_analytics_spec(spec)
print(result["data"])
```

### 2. Execute Natural Language Query

```python
from src.application.services.llm import NLTranslator

# Create translator
translator = NLTranslator(api_key="sk-...")

# Translate and execute
spec = await translator.translate("Show me sprint velocity over the last 6 months")
result = await service.execute_analytics_spec(spec)
```

### 3. Use Predefined Metrics

```python
# Execute predefined metric
result = await service.execute_metric(
    metric_name="sprint_velocity",
    parameters={
        "instance_id": instance_id,
        "start_date": "2024-01-01",
        "end_date": "2024-06-30",
    }
)
```

## AnalyticsSpec Schema

### Structure

```json
{
  "entity": "issues | sprints | comments | changelogs",
  "metrics": [
    {
      "name": "metric_name",
      "aggregation": "sum | avg | count | min | max | median | percentile",
      "field": "field_name",
      "percentile": 0-100
    }
  ],
  "filters": [
    {
      "field": "field_name",
      "operator": "eq | ne | gt | gte | lt | lte | in | not_in | contains | starts_with | ends_with | is_null | is_not_null",
      "value": "any"
    }
  ],
  "group_by": [
    {
      "field": "field_name",
      "interval": "day | week | month | quarter | year"
    }
  ],
  "sort_by": [
    {
      "field": "field_name",
      "direction": "asc | desc"
    }
  ],
  "start_date": "ISO 8601 datetime",
  "end_date": "ISO 8601 datetime",
  "limit": 1-10000,
  "offset": 0+
}
```

### Examples

#### Count Issues by Status

```json
{
  "entity": "issues",
  "metrics": [
    {
      "name": "count",
      "aggregation": "count"
    }
  ],
  "group_by": [
    {
      "field": "status"
    }
  ],
  "sort_by": [
    {
      "field": "count",
      "direction": "desc"
    }
  ]
}
```

#### Average Cycle Time by Issue Type

```json
{
  "entity": "issues",
  "metrics": [
    {
      "name": "avg_cycle_time",
      "aggregation": "avg",
      "field": "cycle_time_days"
    }
  ],
  "filters": [
    {
      "field": "resolved_at",
      "operator": "is_not_null",
      "value": null
    }
  ],
  "group_by": [
    {
      "field": "issue_type"
    }
  ]
}
```

## API Endpoints

### POST /analytics/query

Execute analytics query from AnalyticsSpec.

**Request:**
```json
{
  "entity": "issues",
  "metrics": [{"name": "total", "aggregation": "count"}]
}
```

**Response:**
```json
{
  "data": [...],
  "metadata": {
    "row_count": 10,
    "execution_time_ms": 150,
    "cached": false
  }
}
```

### POST /analytics/query/nl

Execute natural language query.

**Request:**
```json
{
  "query": "Show me sprint velocity over the last 6 months"
}
```

**Response:**
```json
{
  "data": [...],
  "metadata": {...},
  "translated_spec": {...},
  "original_query": "..."
}
```

### GET /analytics/metrics

List available metrics.

**Query Parameters:**
- `category` - Filter by category
- `tags` - Filter by tags (comma-separated)

**Response:**
```json
{
  "metrics": [
    {
      "name": "sprint_velocity",
      "display_name": "Sprint Velocity",
      "description": "...",
      "category": "velocity",
      "unit": "points"
    }
  ],
  "count": 10
}
```

### GET /analytics/metrics/search

Search metrics by name or description.

**Query Parameters:**
- `q` - Search query
- `limit` - Maximum results (1-50)

### POST /analytics/cache/invalidate

Invalidate cache (specific or all).

### GET /analytics/cache/stats

Get cache statistics.

### POST /analytics/cache/cleanup

Clean up expired cache entries.

## Predefined Metrics

### Velocity Metrics
- `sprint_velocity` - Average story points completed per sprint
- `velocity_trend` - Sprint velocity over time with trend line

### Cycle Time Metrics
- `avg_cycle_time` - Average time from in progress to done
- `cycle_time_by_type` - Average cycle time grouped by issue type

### Quality Metrics
- `defect_rate` - Percentage of issues that are bugs
- `reopened_issues` - Number and percentage of reopened issues

### Predictability Metrics
- `commitment_accuracy` - Sprint commitment accuracy

### Throughput Metrics
- `throughput` - Number of issues completed per time period

### Workload Metrics
- `workload_distribution` - Distribution of open issues by assignee

## Caching

The Analytics Engine includes a sophisticated caching system:

- **TTL-based expiration** - Default 24 hours, configurable
- **SHA256 spec hashing** - Deterministic cache keys
- **Automatic invalidation** - Manual or automatic cleanup
- **Cache statistics** - Monitor cache performance

## Security

- **Tenant isolation** - RLS policies on all tables
- **SQL injection prevention** - Parameterized queries only
- **Query validation** - Whitelist of allowed operators and columns
- **Rate limiting** - Configurable limits for interactive vs background jobs

## Performance

- **Materialized views** - Pre-aggregated data for common queries
- **Query caching** - Avoid re-executing identical queries
- **Limit validation** - Prevent expensive queries (1-1000 interactive, 1-100000 jobs)
- **Query cost estimation** - EXPLAIN support for optimization

## Testing

- **71 unit tests** - Models and business logic
- **25 contract tests** - Metrics catalog integrity
- **17 integration tests** - Service integration
- **14 E2E tests** - API endpoints

Total: **127 tests** with >85% coverage

## Development

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# Contract tests
pytest tests/contract/

# With coverage
pytest --cov=src/
```

### Seeding Metrics

```bash
# Seed predefined metrics
python scripts/seed_metrics_catalog.py

# With specific tenant
python scripts/seed_metrics_catalog.py --tenant-id <uuid>
```

### Refreshing Materialized Views

```bash
# Refresh all materialized views
python scripts/refresh_materialized_views.py
```

## Troubleshooting

### Query Validation Errors

If you get validation errors, check:
1. Entity name is valid (issues, sprints, comments, changelogs)
2. Field names are valid for the entity
3. Operators are whitelisted
4. Aggregations have required fields

### Cache Issues

If cache is not working:
1. Check cache stats: `GET /analytics/cache/stats`
2. Invalidate cache: `POST /analytics/cache/invalidate`
3. Clean up expired: `POST /analytics/cache/cleanup`

### Performance Issues

If queries are slow:
1. Check query cost: `POST /analytics/query/validate`
2. Add appropriate filters
3. Use materialized views
4. Enable caching
5. Reduce limit

## Future Enhancements

- [ ] More predefined metrics (target: 25+)
- [ ] Query optimization hints
- [ ] Async job execution for large queries
- [ ] Real-time query streaming
- [ ] Advanced visualization support
- [ ] Query history and favorites
- [ ] Collaborative query sharing

