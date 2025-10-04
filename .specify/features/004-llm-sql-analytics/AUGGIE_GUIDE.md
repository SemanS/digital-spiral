# Auggie Implementation Guide: LLM + SQL Analytics System

## 🎯 Overview

This guide helps Auggie (AI Assistant) implement **Feature 004: LLM + SQL Analytics System** using the Spec-Driven Development methodology.

**Feature**: LLM + SQL Analytics System  
**Timeline**: 12 weeks  
**Methodology**: GitHub Spec-Kit

---

## 📚 Required Reading (Before Starting)

### 1. Constitution (15 min)
Read `.specify/features/004-llm-sql-analytics/constitution.md` to understand:
- Architecture philosophy (Deterministic over Flexible)
- Tech stack (Python, FastAPI, PostgreSQL, Redis, Celery, OpenAI/Claude)
- Code quality standards (Type hints, Pydantic, async/await)
- Security requirements (Whitelisted metrics, RLS, parameterized queries)
- Performance requirements (Materialized views, caching, job orchestration)

### 2. Specification (10 min)
Read `.specify/features/004-llm-sql-analytics/spec.md` to understand:
- User stories (10 total)
- Technical requirements
- API endpoints
- Success metrics

### 3. Implementation Plan (10 min)
Read `.specify/features/004-llm-sql-analytics/plan.md` to understand:
- 6 implementation phases
- Database schema
- File structure
- Testing strategy

### 4. Tasks (5 min)
Read `.specify/features/004-llm-sql-analytics/tasks.md` to understand:
- Task breakdown (30+ tasks)
- Acceptance criteria
- Dependencies
- Estimated effort

---

## 🚀 Quick Start Command

To implement the entire feature, use:

```
/implement
```

This will:
1. Validate prerequisites (constitution, spec, plan, tasks)
2. Parse task breakdown from tasks.md
3. Execute tasks in order, respecting dependencies
4. Follow TDD approach
5. Provide progress updates

---

## 📋 Implementation Workflow

### Phase 1: Foundation (Week 1-2)

#### Week 1: Database Schema & Models

**Task 1.1: Create Migration for Analytics Tables**

```
Auggie, implement Task 1.1: Create Migration for Analytics Tables

Requirements:
- Create migration file: migrations/versions/006_add_analytics_tables.py
- Create 5 tables: sprints, sprint_issues, metrics_catalog, analytics_jobs, analytics_cache
- Add foreign keys with CASCADE delete
- Add indexes for hot paths (tenant_id, instance_id, status, dates)
- Add RLS policies for tenant isolation
- Add unique constraints (instance_id + sprint_id, spec_hash)

Acceptance Criteria:
- [ ] Migration file created
- [ ] All 5 tables created with correct columns and types
- [ ] Foreign keys added with CASCADE delete
- [ ] Indexes created
- [ ] RLS policies applied
- [ ] Unique constraints added
- [ ] Migration runs without errors: alembic upgrade head
- [ ] Migration can be rolled back: alembic downgrade -1

Follow constitution.md standards:
- Type hints mandatory
- Parameterized queries only
- RLS on all tables
```

**Task 1.2: Create SQLAlchemy Models**

```
Auggie, implement Task 1.2: Create SQLAlchemy Models

Requirements:
- Create models for: Sprint, SprintIssue, MetricsCatalog, AnalyticsJob, AnalyticsCache
- Inherit from Base, UUIDMixin, TimestampMixin, TenantMixin
- Add type hints for all columns (Mapped[type])
- Define relationships (sprint ↔ sprint_issues ↔ issues)
- Add docstrings for all models and columns
- Implement __repr__ methods
- Add __table_args__ with indexes and constraints
- Register models in __init__.py

Acceptance Criteria:
- [ ] All models created
- [ ] Type hints for all columns
- [ ] Relationships defined
- [ ] Docstrings added
- [ ] __repr__ methods implemented
- [ ] __table_args__ with indexes
- [ ] Models registered in __init__.py
- [ ] No mypy errors: mypy src/infrastructure/database/models/

Follow constitution.md standards:
- Type hints mandatory (mypy strict mode)
- Pydantic v2 for all DTOs
- Async/await for all I/O operations
```

**Task 1.3: Create Materialized Views**

```
Auggie, implement Task 1.3: Create Materialized Views

Requirements:
- Create mv_sprint_stats_enriched with z-score calculations
- Create mv_issue_comment_stats with comment aggregations
- Add indexes on materialized views
- Create refresh script: scripts/refresh_materialized_views.py
- Configure refresh schedule (cron or Celery beat)

Acceptance Criteria:
- [ ] mv_sprint_stats_enriched created
- [ ] mv_issue_comment_stats created
- [ ] Indexes created
- [ ] Refresh script created
- [ ] Refresh schedule configured
- [ ] Views return correct data
- [ ] Query performance <1s for 10k sprints

Follow constitution.md standards:
- Window functions for z-scores
- GIN indexes for JSONB columns
- Partial indexes for filtered queries
```

**Task 1.4: Write Unit Tests for Models**

```
Auggie, implement Task 1.4: Write Unit Tests for Models

Requirements:
- Create test files for all models
- Test CRUD operations
- Test relationships (sprint ↔ sprint_issues)
- Test validation (unique constraints, foreign keys)
- Test edge cases (null values, cascades)

Acceptance Criteria:
- [ ] Test files created for all models
- [ ] CRUD operations tested
- [ ] Relationship tests
- [ ] Validation tests
- [ ] Edge cases tested
- [ ] 90%+ test coverage: pytest --cov=src/infrastructure/database/models/
- [ ] All tests pass: pytest tests/unit/infrastructure/database/models/

Follow constitution.md standards:
- pytest for unit tests
- 90%+ coverage mandatory
- Test all edge cases
```

#### Week 2: Metrics Catalog

**Task 2.1: Define Core Metrics (25+ metrics)**

```
Auggie, implement Task 2.1: Define Core Metrics

Requirements:
- Create JSON file: scripts/metrics_catalog.json
- Define 25+ metrics across 6 categories:
  - Throughput (4): created, closed, velocity, throughput_ratio
  - Lead Time (4): p50, p90, avg, cycle_time
  - Sprint Health (5): spillover_ratio, scope_churn_ratio, accuracy_abs, planned_sp, completed_sp
  - Quality (4): reopened_count, bug_count, escaped_defects, reopen_rate
  - Capacity (4): blocked_hours, wip, stuck_count, wip_no_assignee
  - Composite (1): sprint_problematic_score
- Each metric must have: name, display_name, description, category, sql_template, dependencies, version

Acceptance Criteria:
- [ ] JSON file created
- [ ] 25+ metrics defined
- [ ] Each metric has all required fields
- [ ] SQL templates are valid
- [ ] Dependencies are valid (no circular dependencies)
- [ ] Weights sum to 1.0 for composite metrics
- [ ] JSON schema validation passes

Follow constitution.md standards:
- Semantic versioning (1.0.0)
- SQL templates must be parameterized
- No SQL injection possible
```

**Task 2.2: Create Metrics Catalog Seeder**

```
Auggie, implement Task 2.2: Create Metrics Catalog Seeder

Requirements:
- Create seeder script: scripts/seed_metrics_catalog.py
- Read metrics from JSON file
- Insert into metrics_catalog table (upsert)
- Validate metric definitions before insert
- Handle duplicates gracefully
- Log progress and errors
- Make idempotent (can run multiple times)

Acceptance Criteria:
- [ ] Seeder script created
- [ ] Reads metrics from JSON
- [ ] Inserts into database (upsert)
- [ ] Validates definitions
- [ ] Handles duplicates
- [ ] Logs progress
- [ ] Idempotent
- [ ] Completes in <10s for 25 metrics

Run command: python scripts/seed_metrics_catalog.py
```

**Task 2.3: Build Metrics Catalog Service**

```
Auggie, implement Task 2.3: Build Metrics Catalog Service

Requirements:
- Create service: src/application/services/analytics/metrics_catalog_service.py
- Implement methods:
  - get_all_metrics() - List all metrics
  - get_metric(name) - Get single metric
  - create_metric(data) - Create new metric (admin)
  - update_metric(name, data) - Update metric (admin)
  - deprecate_metric(name) - Deprecate metric (admin)
- Add validation for metric definitions
- Support versioning (semantic versioning)
- Add deprecation warnings
- Use async methods (async/await)

Acceptance Criteria:
- [ ] Service created
- [ ] All methods implemented
- [ ] Validation for definitions
- [ ] Versioning support
- [ ] Deprecation warnings
- [ ] Async methods
- [ ] Type hints for all methods
- [ ] Docstrings for all methods

Follow constitution.md standards:
- Type hints mandatory
- Pydantic v2 for validation
- Async/await for all I/O
```

**Task 2.4: Write Contract Tests for Metrics Catalog**

```
Auggie, implement Task 2.4: Write Contract Tests for Metrics Catalog

Requirements:
- Create contract test file: tests/contract/test_metrics_catalog_contract.py
- Validate:
  - All metrics have valid SQL templates
  - All dependencies exist in catalog
  - Weights sum to 1.0 for composite metrics
  - No circular dependencies
  - All metrics have version numbers

Acceptance Criteria:
- [ ] Contract test file created
- [ ] All validations implemented
- [ ] All tests pass: pytest tests/contract/

Follow constitution.md standards:
- Contract tests mandatory for metrics catalog
- 100% metrics catalog tested
```

---

## 🔄 Progress Tracking

After each task, provide a report:

```
✅ Task X.Y: [Task Name] (DONE)
   Files Created:
   - [list of files]
   
   Files Updated:
   - [list of files]
   
   Tests:
   - [test files]
   - Coverage: [percentage]
   
   Acceptance Criteria:
   - [X/Y] ✅
   
   Next Task: Task X.Z
```

---

## 🧪 Testing Commands

### Unit Tests
```bash
pytest tests/unit/ -v --cov=src/
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Contract Tests
```bash
pytest tests/contract/ -v
```

### E2E Tests
```bash
pytest tests/e2e/ -v
```

### All Tests
```bash
pytest tests/ -v --cov=src/ --cov-report=html
```

---

## 🔍 Validation Commands

### Type Checking
```bash
mypy src/
```

### Linting
```bash
ruff check src/
```

### Formatting
```bash
ruff format src/
```

### Security
```bash
bandit -r src/
```

---

## 📊 Success Criteria

After each phase, verify:

### Phase 1: Foundation
- [ ] All migrations run successfully
- [ ] All models created and tested (90%+ coverage)
- [ ] Materialized views created and indexed
- [ ] Metrics catalog seeded (25+ metrics)
- [ ] Contract tests pass

### Phase 2: Query Builder
- [ ] AnalyticsSpec schema defined and validated
- [ ] Query builder translates spec to SQL
- [ ] Query executor runs SQL and returns results
- [ ] Caching layer implemented (Redis)
- [ ] 90%+ test coverage

### Phase 3: LLM Integration
- [ ] LLM provider abstraction implemented
- [ ] NL → AnalyticsSpec translator works
- [ ] Semantic search implemented (pgvector)
- [ ] E2E tests pass (NL → Results)

### Phase 4: Job Orchestration
- [ ] Celery setup complete
- [ ] Job manager service implemented
- [ ] Job API endpoints working
- [ ] SSE streaming implemented
- [ ] Integration tests pass

---

## 🚨 Common Issues & Solutions

### Issue: Migration Fails
**Solution**: Check foreign key constraints, ensure parent tables exist

### Issue: Type Errors
**Solution**: Run `mypy src/` and fix all type hints

### Issue: Tests Fail
**Solution**: Check test database setup, ensure fixtures are correct

### Issue: Celery Worker Not Starting
**Solution**: Check Redis connection, ensure broker URL is correct

---

## 📞 Support

If you encounter issues:
1. Check constitution.md for standards
2. Check spec.md for requirements
3. Check plan.md for architecture
4. Check tasks.md for acceptance criteria
5. Open GitHub issue if stuck

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Owner**: Digital Spiral Team

