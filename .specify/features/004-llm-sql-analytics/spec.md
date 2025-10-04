# Feature Specification: LLM + SQL Analytics System

## Overview

Build an AI-powered analytics system that allows users to query Jira data using natural language. The system translates natural language queries into structured AnalyticsSpec (DSL), executes them against a metrics catalog, and returns results with chart recommendations. Designed for multi-tenant, multi-instance Jira deployments with enterprise-grade security and performance.

## Problem Statement

### Current Pain Points
1. **Manual SQL Writing**: Users need SQL expertise to query Jira data
2. **Inconsistent Metrics**: Different teams calculate metrics differently
3. **Performance Issues**: Ad-hoc queries are slow on large datasets
4. **Security Risks**: Raw SQL access creates injection vulnerabilities
5. **Scalability Limits**: Single-instance queries don't scale to multi-tenant

### Target Users
- **Executives**: Need high-level dashboards (sprint health, team velocity)
- **Product Managers**: Need detailed analytics (feature progress, bug trends)
- **Engineering Managers**: Need team metrics (lead time, throughput, quality)
- **Data Analysts**: Need flexible querying without SQL expertise

## User Stories

### US1: User queries data with natural language
**As a** product manager  
**I want to** ask "Show me the most problematic sprints in the last 6 months"  
**So that** I can identify patterns without writing SQL

**Acceptance Criteria**:
- User enters natural language query in chat interface
- LLM translates query to AnalyticsSpec
- System validates spec against metrics catalog
- Results returned in <30s for interactive queries
- Chart recommendation included (bar, line, scatter, etc.)
- Error messages are user-friendly (not technical SQL errors)

**Example Queries**:
- "Find issues with the most comments"
- "Show sprint velocity trend for Project X"
- "Which sprints had the most scope creep?"
- "Compare lead time across teams"

### US2: User views pre-defined metrics catalog
**As a** data analyst  
**I want to** browse available metrics and their definitions  
**So that** I know what data I can query

**Acceptance Criteria**:
- Metrics catalog page lists all metrics
- Each metric shows: name, description, formula, dependencies
- Metrics grouped by category (throughput, quality, capacity)
- Search and filter by category or keyword
- Example queries for each metric
- Version history for metric definitions

**Metrics Categories**:
- **Throughput**: created, closed, velocity, throughput_ratio
- **Lead Time**: p50, p90, avg, cycle_time
- **Sprint Health**: spillover_ratio, scope_churn_ratio, accuracy_abs
- **Quality**: reopened_count, bug_count, escaped_defects
- **Capacity**: blocked_hours, wip, stuck_count
- **Composite**: sprint_problematic_score

### US3: System executes queries with job orchestration
**As a** system  
**I want to** handle large queries asynchronously  
**So that** users don't experience timeouts

**Acceptance Criteria**:
- Queries <30s execute synchronously (analytics.run)
- Queries >30s or multi-instance execute asynchronously (jobs.start)
- Job status endpoint shows progress (queued, running, completed, failed)
- Job result endpoint returns data when ready
- Jobs are idempotent (same spec = same job ID)
- Jobs can be cancelled by user
- Job history retained for 7 days

**Job Flow**:
1. User submits query → LLM generates AnalyticsSpec
2. System estimates query time (based on filters, instances)
3. If <30s → analytics.run (sync)
4. If >30s → jobs.start (async) → return job_id
5. User polls jobs.status(job_id) or subscribes to SSE
6. When complete → jobs.result(job_id) returns data

### US4: User performs semantic search on issues
**As a** engineering manager  
**I want to** search for "sprints with discussions about rollbacks"  
**So that** I can find issues by meaning, not just keywords

**Acceptance Criteria**:
- Semantic search endpoint accepts natural language query
- pgvector indexes issue summaries and comments
- Returns top-K issue IDs ranked by similarity
- Can combine with AnalyticsSpec filters (e.g., "in Project X")
- Search results include similarity score
- Supports multi-language (English, Slovak, Czech)

**Example Searches**:
- "Sprints with discussions about performance issues"
- "Issues related to database migrations"
- "Bugs caused by API changes"

### US5: System renders charts from data
**As a** user  
**I want to** see results visualized automatically  
**So that** I don't need to manually create charts

**Acceptance Criteria**:
- Chart recommendation based on data shape (1D → bar, 2D → scatter, time → line)
- Vega-Lite spec generated for chart
- Supports 10+ chart types: bar, line, scatter, heatmap, box plot, etc.
- Chart config includes: title, axes labels, legend, colors
- User can override chart type
- Charts are responsive and interactive (zoom, pan, tooltip)

**Chart Types**:
- **Bar**: Categorical comparisons (sprint scores, project counts)
- **Line**: Time series (velocity trend, lead time over time)
- **Scatter**: Correlations (story points vs. lead time)
- **Heatmap**: 2D distributions (bugs by project and priority)
- **Box Plot**: Statistical distributions (lead time by team)

### US6: Admin manages metrics catalog
**As an** admin  
**I want to** add/edit/deprecate metrics  
**So that** the catalog stays up-to-date

**Acceptance Criteria**:
- Admin UI for metrics catalog management
- Add new metric: name, description, SQL template, dependencies, weights
- Edit existing metric (creates new version)
- Deprecate metric (shows warning, still works for 2 versions)
- Test metric against sample data before publishing
- Metrics versioned with semantic versioning (1.0.0)
- Audit log for all changes

### US7: User customizes metric weights
**As a** product manager  
**I want to** adjust weights in sprint_problematic_score  
**So that** I can prioritize what matters to my team

**Acceptance Criteria**:
- Default weights: spillover=0.25, churn=0.20, reopened=0.20, blocked=0.15, bugs=0.10, accuracy=0.10
- User can override weights in AnalyticsSpec
- Weights must sum to 1.0 (validation)
- Custom weights saved per user/team
- Comparison view: default vs. custom weights

### US8: System handles multi-instance queries
**As a** user  
**I want to** query across multiple Jira instances  
**So that** I can compare teams/projects

**Acceptance Criteria**:
- AnalyticsSpec accepts list of instance_ids
- Query fan-out: parallel queries per instance
- Results aggregated and merged
- Instance-level errors don't fail entire query
- Partial results returned with warning
- Performance: <5min for 10 instances, 90 days data

### US9: User exports results
**As a** user  
**I want to** export results to CSV/Excel/JSON  
**So that** I can share with stakeholders

**Acceptance Criteria**:
- Export button on results page
- Formats: CSV, Excel (.xlsx), JSON
- Includes metadata: query, timestamp, user
- Large exports (>10k rows) use async jobs
- Download link expires after 24 hours

### US10: System provides query suggestions
**As a** user  
**I want to** see suggested queries based on my data  
**So that** I can discover insights

**Acceptance Criteria**:
- Suggestions based on: recent queries, popular queries, data anomalies
- Categories: "Trending", "Recommended for You", "Anomalies Detected"
- Click suggestion → auto-fill query
- Suggestions updated daily
- Personalized based on user role and projects

## Technical Requirements

### Data Model

#### Core Tables (Existing)
- `issues` - Jira issues with JSONB fields
- `projects` - Jira projects
- `changelogs` - Issue transition history
- `comments` - Issue comments
- `worklogs` - Time tracking

#### New Tables
- `sprints` - Sprint metadata (name, start/end dates, state, board_id)
- `sprint_issues` - Many-to-many: sprint ↔ issues
- `issue_comment_stats` - Derived: issue_id, comment_count, last_comment_at
- `issue_status_durations` - Derived: issue_id, status, seconds
- `sprint_issue_facts` - Derived: sprint_id, issue_id, planned_sp, completed_sp, added_after_start, reopened_count, blocked_seconds
- `sprint_stats` - Derived: sprint_id, planned_sp, completed_sp, spillover_sp, scope_churn_sp, reopened_sum, blocked_sum_seconds, bug_count, escaped_defects
- `metrics_catalog` - Metric definitions (name, description, sql_template, version)
- `analytics_jobs` - Job tracking (job_id, spec, status, result, created_at)
- `analytics_cache` - Query result cache (spec_hash, result, ttl)

#### Materialized Views
- `mv_sprint_stats_enriched` - Sprint stats with z-scores
- `mv_issue_stats_by_assignee` - Aggregated by assignee
- `mv_issue_activity_timeline` - Daily activity metrics
- `mv_changelog_activity_stats` - Changelog aggregations

### AnalyticsSpec DSL

#### Structure
```json
{
  "datasource": "warehouse",
  "measures": [
    {"name": "sprint_problematic_score", "agg": "avg"},
    {"name": "spillover_ratio", "agg": "avg"}
  ],
  "dimensions": ["project_key", "sprint_name", "sprint_id"],
  "filters": [
    {"field": "instance_id", "op": "in", "value": ["inst1", "inst2"]},
    {"field": "sprint_state", "op": "=", "value": "closed"},
    {"field": "ended_at", "op": ">=", "value": "2025-01-01"}
  ],
  "sort": [{"field": "sprint_problematic_score", "dir": "desc"}],
  "limit": 50,
  "chart": {
    "type": "bar",
    "x": "sprint_name",
    "y": "sprint_problematic_score",
    "series": "project_key"
  }
}
```

#### Validation Rules
- `datasource`: Must be "warehouse" (future: "jira_api", "github_api")
- `measures`: 1-10 measures, must exist in catalog
- `dimensions`: 0-5 dimensions, must be valid columns
- `filters`: 0-20 filters, must use whitelisted operators
- `sort`: 0-3 sort fields
- `limit`: 1-1000 (interactive), 1-100000 (jobs)
- `chart`: Optional, must be valid Vega-Lite config

### API Endpoints

#### Analytics Execution
- `POST /analytics/run` - Execute AnalyticsSpec (sync)
  - Request: `{"spec": {...}, "cache": true}`
  - Response: `{"results": [...], "total": 50, "query_time_ms": 123}`
  - Timeout: 30s

- `POST /analytics/jobs` - Start async job
  - Request: `{"spec": {...}}`
  - Response: `{"job_id": "uuid", "status": "queued"}`

- `GET /analytics/jobs/{job_id}` - Job status
  - Response: `{"job_id": "uuid", "status": "running", "progress": 0.5}`

- `GET /analytics/jobs/{job_id}/result` - Job result
  - Response: `{"results": [...], "total": 1000, "query_time_ms": 45000}`

#### Metrics Catalog
- `GET /analytics/metrics` - List all metrics
  - Response: `{"metrics": [...], "total": 25}`

- `GET /analytics/metrics/{name}` - Get metric details
  - Response: `{"name": "...", "description": "...", "sql_template": "...", "version": "1.0.0"}`

- `POST /analytics/metrics` - Create metric (admin only)
- `PUT /analytics/metrics/{name}` - Update metric (admin only)
- `DELETE /analytics/metrics/{name}` - Deprecate metric (admin only)

#### Semantic Search
- `POST /analytics/semantic-search` - Search issues by meaning
  - Request: `{"query": "rollback discussions", "project_keys": ["PROJ1"], "top_k": 10}`
  - Response: `{"issue_ids": ["PROJ1-123", ...], "scores": [0.95, ...]}`

#### Chart Rendering
- `POST /analytics/charts/render` - Generate chart spec
  - Request: `{"data": [...], "chart_type": "bar", "x": "sprint_name", "y": "score"}`
  - Response: `{"vega_spec": {...}}`

### Performance Requirements

#### Query Execution
- **Interactive (<30s)**: 90% of queries
- **Jobs (<5min)**: 99% of queries
- **Timeout**: 30s (interactive), 5min (jobs)
- **Concurrency**: 100 concurrent queries per tenant

#### Caching
- **Cache Hit Rate**: >80% for popular queries
- **TTL**: 5min (default), configurable per query
- **Invalidation**: On data updates (webhooks)
- **Storage**: Redis with LRU eviction

#### Database
- **Query Time**: <1s for cached, <5s for uncached
- **Materialized View Refresh**: Every 15min (incremental)
- **Connection Pool**: 20 connections per worker
- **Indexes**: 80+ indexes on hot paths

## Success Metrics

### Functional
- ✅ 95%+ accuracy for NL → AnalyticsSpec translation
- ✅ 90% of queries complete in <30s
- ✅ 99% of jobs complete in <5min
- ✅ 80%+ semantic search top-5 accuracy
- ✅ 10+ chart types supported

### Performance
- ✅ <100ms p50 latency (cached)
- ✅ <5s p99 latency (uncached)
- ✅ 80%+ cache hit rate
- ✅ 100 concurrent users per tenant
- ✅ Scales to 100 tenants, 1M issues

### Quality
- ✅ 90%+ test coverage
- ✅ Zero SQL injection vulnerabilities
- ✅ <5% error rate in production
- ✅ 99.9% uptime (3 nines)

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

