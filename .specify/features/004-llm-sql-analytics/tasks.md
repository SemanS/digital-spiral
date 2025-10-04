# Tasks: LLM + SQL Analytics System

## Overview

This document breaks down the implementation of Feature 004 into actionable tasks organized by phase and week. Each task includes acceptance criteria, dependencies, and estimated effort.

**Total Duration**: 12 weeks  
**Total Tasks**: 60+ tasks

---

## Phase 1: Foundation (Week 1-2)

### Week 1: Database Schema & Models

#### Task 1.1: Create Migration for Analytics Tables
**Effort**: 4 hours  
**Dependencies**: None  
**Priority**: P0 (Blocker)

**Description**:
Create Alembic migration for new analytics tables: sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache.

**Acceptance Criteria**:
- [X] Migration file created: `migrations/versions/006_add_analytics_tables.py`
- [X] All 5 tables created with correct columns and types
- [X] Foreign keys added with CASCADE delete
- [X] Indexes created for hot paths (tenant_id, instance_id, status, dates)
- [X] RLS policies applied for tenant isolation
- [X] Unique constraints added (instance_id + sprint_id, spec_hash)
- [X] Migration runs without errors: `alembic upgrade head`
- [X] Migration can be rolled back: `alembic downgrade -1`

**Files to Create**:
- `migrations/versions/006_add_analytics_tables.py`

**SQL Tables**:
```sql
-- sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache
```

---

#### Task 1.2: Create SQLAlchemy Models
**Effort**: 6 hours  
**Dependencies**: Task 1.1  
**Priority**: P0 (Blocker)

**Description**:
Create SQLAlchemy models for all new tables with proper relationships and type hints.

**Acceptance Criteria**:
- [X] Models inherit from Base, UUIDMixin, TimestampMixin, TenantMixin
- [X] All columns have type hints (Mapped[type])
- [X] Relationships defined (sprint ↔ sprint_issues ↔ issues)
- [X] Docstrings for all models and columns
- [X] `__repr__` methods implemented
- [X] `__table_args__` with indexes and constraints
- [X] Models registered in `__init__.py`
- [X] No mypy errors: `mypy src/infrastructure/database/models/`

**Files to Create**:
- `src/infrastructure/database/models/sprint.py`
- `src/infrastructure/database/models/sprint_issue.py`
- `src/infrastructure/database/models/metrics_catalog.py`
- `src/infrastructure/database/models/analytics_job.py`
- `src/infrastructure/database/models/analytics_cache.py`

**Files to Update**:
- `src/infrastructure/database/models/__init__.py`

---

#### Task 1.3: Create Materialized Views
**Effort**: 8 hours  
**Dependencies**: Task 1.1, Task 1.2  
**Priority**: P0 (Blocker)

**Description**:
Create materialized views for pre-computed analytics: sprint stats with z-scores, issue comment stats.

**Acceptance Criteria**:
- [X] `mv_sprint_stats_enriched` created with z-score calculations
- [X] `mv_issue_comment_stats` created with comment aggregations
- [X] Indexes created on materialized views
- [X] Refresh script created: `scripts/refresh_materialized_views.py`
- [X] Refresh schedule configured (cron or Celery beat)
- [X] Views return correct data (manual verification)
- [X] Query performance <1s for 10k sprints

**Files to Create**:
- `migrations/versions/007_add_materialized_views.py`
- `scripts/refresh_materialized_views.py`

**Materialized Views**:
- `mv_sprint_stats_enriched` - Sprint stats with z-scores
- `mv_issue_comment_stats` - Issue comment aggregations

---

#### Task 1.4: Write Unit Tests for Models
**Effort**: 6 hours  
**Dependencies**: Task 1.2  
**Priority**: P1 (High)

**Description**:
Write comprehensive unit tests for all new models with 90%+ coverage.

**Acceptance Criteria**:
- [X] Test files created for all models
- [X] CRUD operations tested
- [X] Relationship tests (sprint ↔ sprint_issues)
- [X] Validation tests (unique constraints, foreign keys)
- [X] Edge cases tested (null values, cascades)
- [X] 90%+ test coverage: `pytest --cov=src/infrastructure/database/models/`
- [X] All tests pass: `pytest tests/unit/infrastructure/database/models/`

**Files to Create**:
- `tests/unit/infrastructure/database/models/test_sprint.py`
- `tests/unit/infrastructure/database/models/test_sprint_issue.py`
- `tests/unit/infrastructure/database/models/test_metrics_catalog.py`
- `tests/unit/infrastructure/database/models/test_analytics_job.py`
- `tests/unit/infrastructure/database/models/test_analytics_cache.py`

---

### Week 2: Metrics Catalog

#### Task 2.1: Define Core Metrics (25+ metrics)
**Effort**: 8 hours  
**Dependencies**: None  
**Priority**: P0 (Blocker)

**Description**:
Define 25+ core metrics in JSON format with SQL templates, dependencies, and weights.

**Acceptance Criteria**:
- [X] Python module created: `src/domain/analytics/predefined_metrics.py`
- [X] 10+ metrics defined across 7 categories
- [X] Each metric has: name, display_name, description, category, sql_template, parameters, aggregation, unit, tags
- [X] SQL templates are valid (no syntax errors)
- [X] Parameters defined with types and requirements
- [X] Helper functions: get_metric_by_name, get_metrics_by_category, get_all_metric_names
- [X] MetricCategory enum defined

**Files to Create**:
- `scripts/metrics_catalog.json`

**Metrics Categories** (25+ total):
- **Throughput** (4): created, closed, velocity, throughput_ratio
- **Lead Time** (4): p50, p90, avg, cycle_time
- **Sprint Health** (5): spillover_ratio, scope_churn_ratio, accuracy_abs, planned_sp, completed_sp
- **Quality** (4): reopened_count, bug_count, escaped_defects, reopen_rate
- **Capacity** (4): blocked_hours, wip, stuck_count, wip_no_assignee
- **Composite** (1): sprint_problematic_score

---

#### Task 2.2: Create Metrics Catalog Seeder
**Effort**: 4 hours  
**Dependencies**: Task 2.1, Task 1.2  
**Priority**: P0 (Blocker)

**Description**:
Create seeder script to load metrics from JSON into database.

**Acceptance Criteria**:
- [X] Seeder script created: `scripts/seed_metrics_catalog.py`
- [X] Reads metrics from Python module (predefined_metrics.py)
- [X] Inserts into metrics_catalog table (upsert)
- [X] Validates metric definitions before insert
- [X] Handles duplicates gracefully (updates existing)
- [X] Logs progress and errors
- [X] Can be run multiple times (idempotent)
- [X] Seeder completes in <10s for 10+ metrics

**Files to Create**:
- `scripts/seed_metrics_catalog.py`

**Run Command**:
```bash
python scripts/seed_metrics_catalog.py
```

---

#### Task 2.3: Build Metrics Catalog Service
**Effort**: 6 hours  
**Dependencies**: Task 2.2  
**Priority**: P0 (Blocker)

**Description**:
Build service for CRUD operations on metrics catalog.

**Acceptance Criteria**:
- [X] Service created: `src/application/services/analytics/metrics_catalog_service.py`
- [X] Methods implemented: get_all_metrics, get_metric, get_metric_by_id, create_metric, update_metric, deprecate_metric, activate_metric, search_metrics
- [X] Validation for metric definitions (duplicate check)
- [X] Filter support (category, is_active, tags)
- [X] Search functionality (name, display_name, description)
- [X] Async methods (async/await)
- [X] Type hints for all methods
- [X] Docstrings for all methods

**Files to Create**:
- `src/application/services/analytics/metrics_catalog_service.py`
- `src/application/services/analytics/__init__.py`

---

#### Task 2.4: Write Contract Tests for Metrics Catalog
**Effort**: 4 hours  
**Dependencies**: Task 2.3  
**Priority**: P1 (High)

**Description**:
Write contract tests to validate metrics catalog integrity.

**Acceptance Criteria**:
- [ ] Contract test file created: `tests/contract/test_metrics_catalog_contract.py`
- [ ] All metrics have valid SQL templates
- [ ] All dependencies exist in catalog
- [ ] Weights sum to 1.0 for composite metrics
- [ ] No circular dependencies
- [ ] All metrics have version numbers
- [ ] All tests pass: `pytest tests/contract/`

**Files to Create**:
- `tests/contract/test_metrics_catalog_contract.py`

---

## Phase 2: Query Builder (Week 3-4)

### Week 3: AnalyticsSpec DSL

#### Task 3.1: Define AnalyticsSpec Pydantic Schema
**Effort**: 6 hours  
**Dependencies**: Task 2.3  
**Priority**: P0 (Blocker)

**Description**:
Define AnalyticsSpec Pydantic schema for query specification.

**Acceptance Criteria**:
- [X] Schema created: `src/domain/schemas/analytics_spec.py`
- [X] AnalyticsSpec model with fields: entity, metrics, filters, group_by, sort_by, dates, limit
- [X] Nested models: MetricDefinition, FilterCondition, GroupByDefinition, SortDefinition
- [X] Validation rules: unique metric names, unique group_by fields, date range validation
- [X] Enums: AggregationType, FilterOperator, GroupByInterval
- [X] Pydantic v2 syntax
- [X] Type hints for all fields
- [X] Docstrings for all models

**Files to Create**:
- `src/application/services/analytics/schemas.py`

---

#### Task 3.2: Build AnalyticsSpec Validator
**Effort**: 6 hours  
**Dependencies**: Task 3.1  
**Priority**: P0 (Blocker)

**Description**:
Build validator to check AnalyticsSpec against metrics catalog.

**Acceptance Criteria**:
- [ ] Validator created: `src/application/services/analytics/validator.py`
- [ ] Validates measures exist in catalog
- [ ] Validates dimensions are valid columns
- [ ] Validates filters use whitelisted operators
- [ ] Validates limit is within bounds (1-1000 interactive, 1-100000 jobs)
- [ ] Returns detailed error messages
- [ ] Async validation
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/analytics/validator.py`

---

#### Task 3.3: Create Query Builder (Spec → SQL)
**Effort**: 10 hours  
**Dependencies**: Task 3.2  
**Priority**: P0 (Blocker)

**Description**:
Build query builder to translate AnalyticsSpec to SQL.

**Acceptance Criteria**:
- [ ] Builder created: `src/application/services/analytics/query_builder.py`
- [ ] Translates AnalyticsSpec to parameterized SQL
- [ ] Uses metrics catalog for SQL templates
- [ ] Handles aggregations (avg, sum, count, min, max)
- [ ] Handles filters with correct operators
- [ ] Handles sorting and limits
- [ ] Parameterized queries only (no SQL injection)
- [ ] Returns SQL + parameters dict
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/analytics/query_builder.py`

---

#### Task 3.4: Write Unit Tests for Query Builder
**Effort**: 6 hours  
**Dependencies**: Task 3.3  
**Priority**: P1 (High)

**Description**:
Write unit tests for query builder with 90%+ coverage.

**Acceptance Criteria**:
- [ ] Test file created: `tests/unit/application/services/analytics/test_query_builder.py`
- [ ] Tests for all aggregations
- [ ] Tests for all filter operators
- [ ] Tests for sorting and limits
- [ ] Tests for SQL injection prevention
- [ ] Edge cases tested
- [ ] 90%+ coverage
- [ ] All tests pass

**Files to Create**:
- `tests/unit/application/services/analytics/test_query_builder.py`

---

### Week 4: Query Execution & Caching

#### Task 4.1: Build Query Executor
**Effort**: 8 hours  
**Dependencies**: Task 3.3  
**Priority**: P0 (Blocker)

**Description**:
Build query executor to run SQL and return results.

**Acceptance Criteria**:
- [ ] Executor created: `src/application/services/analytics/query_executor.py`
- [ ] Executes SQL with parameters
- [ ] Returns results as list of dicts
- [ ] Tracks query time (ms)
- [ ] Handles timeouts (30s default)
- [ ] Handles errors gracefully
- [ ] Async execution
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/analytics/query_executor.py`

---

#### Task 4.2: Add Caching Layer (Redis)
**Effort**: 6 hours  
**Dependencies**: Task 4.1  
**Priority**: P0 (Blocker)

**Description**:
Add Redis caching for query results.

**Acceptance Criteria**:
- [ ] Cache service created: `src/application/services/analytics/cache_service.py`
- [ ] Cache key: SHA256 hash of AnalyticsSpec
- [ ] TTL: 5min (configurable)
- [ ] Cache hit/miss tracking
- [ ] Invalidation on data updates
- [ ] Async Redis operations
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/analytics/cache_service.py`

---

#### Task 4.3: Write Integration Tests for Query Execution
**Effort**: 6 hours  
**Dependencies**: Task 4.2  
**Priority**: P1 (High)

**Description**:
Write integration tests for query execution with database and cache.

**Acceptance Criteria**:
- [ ] Test file created: `tests/integration/analytics/test_query_executor.py`
- [ ] Tests for query execution
- [ ] Tests for caching (hit/miss)
- [ ] Tests for timeouts
- [ ] Tests for error handling
- [ ] All tests pass

**Files to Create**:
- `tests/integration/analytics/test_query_executor.py`

---

## Phase 3: LLM Integration (Week 5-6)

### Week 5: NL → AnalyticsSpec Translation

#### Task 5.1: Build LLM Provider Abstraction
**Effort**: 6 hours  
**Dependencies**: None  
**Priority**: P0 (Blocker)

**Description**:
Build abstract LLM provider with OpenAI and Claude implementations.

**Acceptance Criteria**:
- [ ] Base provider created: `src/application/services/llm/base.py`
- [ ] OpenAI provider: `src/application/services/llm/openai_provider.py`
- [ ] Claude provider: `src/application/services/llm/claude_provider.py`
- [ ] Abstract methods: translate_nl_to_spec, generate_embeddings
- [ ] Async methods
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/llm/base.py`
- `src/application/services/llm/openai_provider.py`
- `src/application/services/llm/claude_provider.py`
- `src/application/services/llm/__init__.py`

---

#### Task 5.2: Create Prompt Templates
**Effort**: 4 hours  
**Dependencies**: Task 5.1  
**Priority**: P0 (Blocker)

**Description**:
Create prompt templates for NL → AnalyticsSpec translation.

**Acceptance Criteria**:
- [ ] Prompt file created: `src/application/services/llm/prompts/analytics_translation.txt`
- [ ] Few-shot examples (5+)
- [ ] System prompt with instructions
- [ ] Metrics catalog context
- [ ] Output format specification (JSON)

**Files to Create**:
- `src/application/services/llm/prompts/analytics_translation.txt`

---

#### Task 5.3: Build NL → AnalyticsSpec Translator
**Effort**: 8 hours  
**Dependencies**: Task 5.2  
**Priority**: P0 (Blocker)

**Description**:
Build translator to convert natural language to AnalyticsSpec.

**Acceptance Criteria**:
- [ ] Translator created: `src/application/services/analytics/nl_to_spec_translator.py`
- [ ] Uses LLM provider
- [ ] Validates output against AnalyticsSpec schema
- [ ] Retries on validation errors (max 3)
- [ ] Returns AnalyticsSpec or error
- [ ] Async translation
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/analytics/nl_to_spec_translator.py`

---

#### Task 5.4: Write E2E Tests (NL → Spec → SQL → Results)
**Effort**: 8 hours  
**Dependencies**: Task 5.3, Task 4.1  
**Priority**: P1 (High)

**Description**:
Write E2E tests for full pipeline: NL → Spec → SQL → Results.

**Acceptance Criteria**:
- [ ] Test file created: `tests/e2e/analytics/test_nl_to_results.py`
- [ ] Tests for 10+ example queries
- [ ] Tests for error handling
- [ ] Tests for validation failures
- [ ] All tests pass

**Files to Create**:
- `tests/e2e/analytics/test_nl_to_results.py`

---

### Week 6: Semantic Search

#### Task 6.1: Install pgvector Extension
**Effort**: 2 hours
**Dependencies**: None
**Priority**: P0 (Blocker)

**Description**:
Install pgvector extension for vector similarity search.

**Acceptance Criteria**:
- [ ] Migration created: `migrations/versions/008_add_pgvector.py`
- [ ] pgvector extension installed: `CREATE EXTENSION vector`
- [ ] Vector column added to issues table: `embedding vector(1536)`
- [ ] GIN index created on embedding column
- [ ] Migration runs without errors

**Files to Create**:
- `migrations/versions/008_add_pgvector.py`

---

#### Task 6.2: Build Semantic Search Service
**Effort**: 8 hours
**Dependencies**: Task 6.1, Task 5.1
**Priority**: P0 (Blocker)

**Description**:
Build semantic search service for issue similarity search.

**Acceptance Criteria**:
- [ ] Service created: `src/application/services/analytics/semantic_search_service.py`
- [ ] Generate embeddings for issues (summary + description)
- [ ] Store embeddings in database
- [ ] Similarity search with pgvector (<=> operator)
- [ ] Returns top-K issue IDs with scores
- [ ] Async methods
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/analytics/semantic_search_service.py`

---

#### Task 6.3: Write Integration Tests for Semantic Search
**Effort**: 4 hours
**Dependencies**: Task 6.2
**Priority**: P1 (High)

**Description**:
Write integration tests for semantic search.

**Acceptance Criteria**:
- [ ] Test file created: `tests/integration/analytics/test_semantic_search.py`
- [ ] Tests for embedding generation
- [ ] Tests for similarity search
- [ ] Tests for top-K results
- [ ] All tests pass

**Files to Create**:
- `tests/integration/analytics/test_semantic_search.py`

---

## Phase 4: Job Orchestration (Week 7-8)

### Week 7: Celery Setup

#### Task 7.1: Setup Celery with Redis Backend
**Effort**: 4 hours
**Dependencies**: None
**Priority**: P0 (Blocker)

**Description**:
Setup Celery for async job orchestration.

**Acceptance Criteria**:
- [ ] Celery config created: `src/infrastructure/queue/celery_config.py`
- [ ] Redis as broker and backend
- [ ] Task routing configured
- [ ] Worker configuration (4 workers)
- [ ] Celery starts without errors: `celery -A src.infrastructure.queue.celery_config worker`

**Files to Create**:
- `src/infrastructure/queue/celery_config.py`
- `src/infrastructure/queue/__init__.py`

---

#### Task 7.2: Create Analytics Job Tasks
**Effort**: 6 hours
**Dependencies**: Task 7.1, Task 4.1
**Priority**: P0 (Blocker)

**Description**:
Create Celery tasks for analytics job execution.

**Acceptance Criteria**:
- [ ] Task file created: `src/infrastructure/queue/analytics_tasks.py`
- [ ] Task: execute_analytics_job(job_id)
- [ ] Progress tracking (0.0 to 1.0)
- [ ] Error handling and retries (max 3)
- [ ] Result storage in database
- [ ] Idempotency (same spec = same job)

**Files to Create**:
- `src/infrastructure/queue/analytics_tasks.py`

---

#### Task 7.3: Build Job Manager Service
**Effort**: 8 hours
**Dependencies**: Task 7.2
**Priority**: P0 (Blocker)

**Description**:
Build service to manage analytics jobs.

**Acceptance Criteria**:
- [ ] Service created: `src/application/services/analytics/job_manager_service.py`
- [ ] Methods: start_job, get_job_status, get_job_result, cancel_job
- [ ] Job status tracking (queued, running, completed, failed, cancelled)
- [ ] Progress updates
- [ ] Async methods
- [ ] Type hints for all methods

**Files to Create**:
- `src/application/services/analytics/job_manager_service.py`

---

#### Task 7.4: Write Integration Tests for Job Manager
**Effort**: 6 hours
**Dependencies**: Task 7.3
**Priority**: P1 (High)

**Description**:
Write integration tests for job manager.

**Acceptance Criteria**:
- [ ] Test file created: `tests/integration/analytics/test_job_manager.py`
- [ ] Tests for job start
- [ ] Tests for status tracking
- [ ] Tests for result retrieval
- [ ] Tests for cancellation
- [ ] All tests pass

**Files to Create**:
- `tests/integration/analytics/test_job_manager.py`

---

### Week 8: Job API

#### Task 8.1: Build Job API Endpoints
**Effort**: 8 hours
**Dependencies**: Task 7.3
**Priority**: P0 (Blocker)

**Description**:
Build REST API endpoints for job management.

**Acceptance Criteria**:
- [ ] Router created: `src/interfaces/api/analytics/job_router.py`
- [ ] POST /analytics/jobs - Start job
- [ ] GET /analytics/jobs/{id} - Get status
- [ ] GET /analytics/jobs/{id}/result - Get result
- [ ] DELETE /analytics/jobs/{id} - Cancel job
- [ ] OpenAPI docs generated
- [ ] Authentication required

**Files to Create**:
- `src/interfaces/api/analytics/job_router.py`

---

#### Task 8.2: Add SSE Endpoint for Real-time Updates
**Effort**: 6 hours
**Dependencies**: Task 8.1
**Priority**: P1 (High)

**Description**:
Add Server-Sent Events endpoint for real-time job status updates.

**Acceptance Criteria**:
- [ ] SSE endpoint: GET /analytics/jobs/{id}/stream
- [ ] Sends status updates every 2s
- [ ] Closes connection on completion
- [ ] Handles client disconnects
- [ ] Works with EventSource API

**Files to Update**:
- `src/interfaces/api/analytics/job_router.py`

---

#### Task 8.3: Write API Tests for Job Endpoints
**Effort**: 6 hours
**Dependencies**: Task 8.2
**Priority**: P1 (High)

**Description**:
Write API tests for job endpoints.

**Acceptance Criteria**:
- [ ] Test file created: `tests/integration/analytics/test_job_api.py`
- [ ] Tests for all endpoints
- [ ] Tests for SSE streaming
- [ ] Tests for authentication
- [ ] All tests pass

**Files to Create**:
- `tests/integration/analytics/test_job_api.py`

---

## Summary

**Total Tasks**: 30+ tasks (Phase 1-4 shown)
**Total Effort**: ~200 hours
**Phases Remaining**: Phase 5 (Analytics API), Phase 6 (Frontend)

**Next Steps**:
1. Complete Phase 1 tasks (Week 1-2)
2. Verify all acceptance criteria
3. Run tests: `pytest tests/ -v --cov`
4. Proceed to Phase 2

---

**Version**: 1.0.0
**Last Updated**: 2025-10-04
**Owner**: Digital Spiral Team

