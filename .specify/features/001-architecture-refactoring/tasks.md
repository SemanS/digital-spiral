# Tasks: Architecture Refactoring

## Phase 1: Foundation (Week 1-2)

### Task 1.1: Create New Directory Structure
**Estimate**: 1 hour  
**Priority**: Critical  
**Dependencies**: None

**Description**: Create the new layered architecture directory structure.

**Acceptance Criteria**:
- [ ] Create `src/domain/` with subdirectories: `entities/`, `value_objects/`, `services/`, `events/`
- [ ] Create `src/application/` with subdirectories: `use_cases/`, `dtos/`, `services/`
- [ ] Create `src/infrastructure/` with subdirectories: `database/`, `cache/`, `queue/`, `external/`, `observability/`, `config/`
- [ ] Create `src/interfaces/` with subdirectories: `rest/`, `mcp/`, `sql/`
- [ ] Create `migrations/` for Alembic
- [ ] Add `__init__.py` files to all packages
- [ ] Update `.gitignore` to exclude `__pycache__`, `.pytest_cache`, etc.

---

### Task 1.2: Set Up PostgreSQL with Docker Compose
**Estimate**: 2 hours  
**Priority**: Critical  
**Dependencies**: Task 1.1

**Description**: Configure PostgreSQL database with Docker Compose for local development.

**Acceptance Criteria**:
- [ ] Create `docker/docker-compose.dev.yml` with PostgreSQL 14+ service
- [ ] Configure PostgreSQL with JSONB support and extensions (uuid-ossp, pg_trgm)
- [ ] Add Redis 6+ service for caching
- [ ] Add environment variables for database connection
- [ ] Create health check for PostgreSQL
- [ ] Add volume mounts for data persistence
- [ ] Document connection strings in README

---

### Task 1.3: Set Up Alembic for Database Migrations
**Estimate**: 2 hours  
**Priority**: Critical  
**Dependencies**: Task 1.2

**Description**: Initialize Alembic for database schema migrations.

**Acceptance Criteria**:
- [ ] Install Alembic: `pip install alembic`
- [ ] Run `alembic init migrations`
- [ ] Configure `alembic.ini` with database URL from environment
- [ ] Create `migrations/env.py` with SQLAlchemy metadata import
- [ ] Create initial migration: `alembic revision --autogenerate -m "Initial schema"`
- [ ] Test migration: `alembic upgrade head`
- [ ] Test rollback: `alembic downgrade -1`
- [ ] Document migration commands in README

---

### Task 1.4: Create Base SQLAlchemy Models
**Estimate**: 3 hours  
**Priority**: Critical  
**Dependencies**: Task 1.3

**Description**: Create base SQLAlchemy models and configuration.

**Acceptance Criteria**:
- [ ] Create `src/infrastructure/database/models/base.py` with Base class
- [ ] Add `TimestampMixin` for `created_at`, `updated_at` fields
- [ ] Add `UUIDMixin` for UUID primary keys
- [ ] Create `Tenant` model in `src/infrastructure/database/models/tenant.py`
- [ ] Create `JiraInstance` model in `src/infrastructure/database/models/jira_instance.py`
- [ ] Add relationships between Tenant and JiraInstance
- [ ] Create database session factory
- [ ] Add type hints to all models
- [ ] Write unit tests for model creation

---

### Task 1.5: Create Domain Entities
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: None (pure Python)

**Description**: Create pure Python domain entities without framework dependencies.

**Acceptance Criteria**:
- [ ] Create `src/domain/entities/issue.py` with Issue entity
- [ ] Create `src/domain/entities/project.py` with Project entity
- [ ] Create `src/domain/entities/user.py` with User entity
- [ ] Create `src/domain/entities/comment.py` with Comment entity
- [ ] Create `src/domain/entities/changelog.py` with Changelog entity
- [ ] Add type hints and dataclasses
- [ ] Add validation methods (e.g., `is_valid_issue_key()`)
- [ ] Add business logic methods (e.g., `can_transition_to()`)
- [ ] Write unit tests for each entity (80%+ coverage)

---

### Task 1.6: Set Up Redis for Caching
**Estimate**: 2 hours  
**Priority**: High  
**Dependencies**: Task 1.2

**Description**: Configure Redis client and caching infrastructure.

**Acceptance Criteria**:
- [ ] Add Redis to `docker-compose.dev.yml`
- [ ] Install `redis` package: `pip install redis`
- [ ] Create `src/infrastructure/cache/redis_client.py` with connection pool
- [ ] Create `src/infrastructure/cache/cache_service.py` with get/set/delete methods
- [ ] Add TTL support for cache entries
- [ ] Add cache key namespacing (e.g., `tenant:{id}:issue:{key}`)
- [ ] Write unit tests with fakeredis
- [ ] Document caching strategy in README

---

### Task 1.7: Configure Logging, Metrics, Tracing
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 1.1

**Description**: Set up observability infrastructure (logging, metrics, tracing).

**Acceptance Criteria**:
- [ ] Create `src/infrastructure/observability/logger.py` with structured logging
- [ ] Configure JSON log format with request ID, tenant ID, user ID
- [ ] Create `src/infrastructure/observability/metrics.py` with Prometheus client
- [ ] Add metrics: request_count, request_duration, error_count
- [ ] Create `src/infrastructure/observability/tracer.py` with OpenTelemetry
- [ ] Add trace context propagation
- [ ] Create `/metrics` endpoint for Prometheus scraping
- [ ] Write tests for logging and metrics

---

### Task 1.8: Create Base Repository Interfaces
**Estimate**: 2 hours  
**Priority**: High  
**Dependencies**: Task 1.5

**Description**: Define abstract repository interfaces in application layer.

**Acceptance Criteria**:
- [ ] Create `src/application/interfaces/repository.py` with base Repository protocol
- [ ] Define methods: `get_by_id()`, `get_all()`, `create()`, `update()`, `delete()`
- [ ] Create `IssueRepository` interface
- [ ] Create `ProjectRepository` interface
- [ ] Create `UserRepository` interface
- [ ] Add type hints with generics
- [ ] Document repository pattern in README

---

## Phase 2: Data Layer (Week 3-4)

### Task 2.1: Create All SQLAlchemy Models
**Estimate**: 6 hours  
**Priority**: Critical  
**Dependencies**: Task 1.4

**Description**: Implement complete database schema with all tables.

**Acceptance Criteria**:
- [ ] Create `Project` model with relationships
- [ ] Create `User` model with email hashing
- [ ] Create `Issue` model with JSONB fields
- [ ] Create `IssueLink` model for issue relationships
- [ ] Create `Comment` model with ADF support
- [ ] Create `Changelog` model for history tracking
- [ ] Create `CustomField` model for metadata
- [ ] Create `SyncWatermark` model for incremental sync
- [ ] Create `AuditLog` model for write operations
- [ ] Add all foreign key relationships
- [ ] Add cascade delete rules
- [ ] Write Alembic migration
- [ ] Test migration up/down

---

### Task 2.2: Implement Repository Pattern
**Estimate**: 8 hours  
**Priority**: Critical  
**Dependencies**: Task 2.1, Task 1.8

**Description**: Implement concrete repository classes for each entity.

**Acceptance Criteria**:
- [ ] Create `src/infrastructure/database/repositories/issue_repository.py`
- [ ] Implement `IssueRepository` with CRUD operations
- [ ] Add `search()` method with filters (status, assignee, project, etc.)
- [ ] Add `get_by_key()` method for issue key lookup
- [ ] Create `ProjectRepository` with CRUD operations
- [ ] Create `UserRepository` with CRUD operations
- [ ] Create `CommentRepository` with CRUD operations
- [ ] Create `ChangelogRepository` with CRUD operations
- [ ] Add pagination support (limit, offset)
- [ ] Add sorting support
- [ ] Write unit tests for each repository (80%+ coverage)
- [ ] Use in-memory SQLite for tests

---

### Task 2.3: Create Database Indexes
**Estimate**: 2 hours  
**Priority**: High  
**Dependencies**: Task 2.1

**Description**: Add database indexes for query performance.

**Acceptance Criteria**:
- [ ] Add B-tree indexes on foreign keys
- [ ] Add B-tree indexes on frequently queried columns (status, assignee, created_at)
- [ ] Add GIN indexes on JSONB columns (`raw_jsonb`)
- [ ] Add GIN indexes on array columns (`labels`, `sprint_ids`)
- [ ] Add partial indexes for common filters (e.g., `WHERE active = TRUE`)
- [ ] Create Alembic migration for indexes
- [ ] Test query performance with EXPLAIN ANALYZE
- [ ] Document indexing strategy

---

### Task 2.4: Implement Row-Level Security (RLS)
**Estimate**: 4 hours  
**Priority**: Critical  
**Dependencies**: Task 2.1

**Description**: Implement PostgreSQL RLS policies for multi-tenant isolation.

**Acceptance Criteria**:
- [ ] Enable RLS on all tenant-scoped tables
- [ ] Create RLS policy for `jira_instances` table
- [ ] Create RLS policy for `projects` table
- [ ] Create RLS policy for `issues` table
- [ ] Create RLS policy for `comments` table
- [ ] Create RLS policy for `changelogs` table
- [ ] Add `SET app.current_tenant_id = '<tenant_id>'` in session
- [ ] Test RLS policies with multiple tenants
- [ ] Write integration tests for tenant isolation
- [ ] Document RLS setup in README

---

### Task 2.5: Create Materialized Views
**Estimate**: 3 hours  
**Priority**: Medium  
**Dependencies**: Task 2.1

**Description**: Create materialized views for pre-computed metrics.

**Acceptance Criteria**:
- [ ] Create `issue_metrics` materialized view (count by status, project)
- [ ] Create `lead_time_view` materialized view (from changelog)
- [ ] Create `user_workload_view` materialized view (issues per assignee)
- [ ] Add unique indexes on materialized views
- [ ] Create refresh function: `REFRESH MATERIALIZED VIEW CONCURRENTLY`
- [ ] Create Celery task for periodic refresh (every 5 minutes)
- [ ] Write Alembic migration for views
- [ ] Test view queries

---

### Task 2.6: Implement Caching Layer
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 1.6, Task 2.2

**Description**: Add caching to repository layer for frequently accessed data.

**Acceptance Criteria**:
- [ ] Wrap repository methods with cache decorator
- [ ] Cache issue lookups by key (TTL: 5 minutes)
- [ ] Cache project lookups by key (TTL: 10 minutes)
- [ ] Cache user lookups by account_id (TTL: 10 minutes)
- [ ] Implement cache invalidation on write operations
- [ ] Add cache hit/miss metrics
- [ ] Write tests for cache behavior
- [ ] Document caching strategy

---

### Task 2.7: Write Unit Tests for Repositories
**Estimate**: 6 hours  
**Priority**: High  
**Dependencies**: Task 2.2

**Description**: Comprehensive unit tests for all repository implementations.

**Acceptance Criteria**:
- [ ] Test CRUD operations for each repository
- [ ] Test search with various filters
- [ ] Test pagination and sorting
- [ ] Test error handling (not found, duplicate, etc.)
- [ ] Test transaction rollback
- [ ] Test concurrent access
- [ ] Achieve 80%+ code coverage
- [ ] Use pytest fixtures for test data

---

### Task 2.8: Create Seed Data for Testing
**Estimate**: 3 hours  
**Priority**: Medium  
**Dependencies**: Task 2.1

**Description**: Create realistic seed data for development and testing.

**Acceptance Criteria**:
- [ ] Create `scripts/seed_database.py` script
- [ ] Generate 3 tenants with 2 Jira instances each
- [ ] Generate 10 projects per instance
- [ ] Generate 100 issues per project with realistic data
- [ ] Generate comments and changelogs for issues
- [ ] Generate users with hashed emails
- [ ] Add command-line arguments for data volume
- [ ] Document seed script usage

---

## Phase 3: Sync Layer (Week 5-6)

### Task 3.1: Create Jira API Client
**Estimate**: 6 hours  
**Priority**: Critical  
**Dependencies**: Task 1.1

**Description**: Implement HTTP client for Jira Cloud REST API.

**Acceptance Criteria**:
- [ ] Create `src/infrastructure/external/jira_client.py` using httpx
- [ ] Implement authentication (Basic Auth with API token)
- [ ] Add methods: `get_issue()`, `search_issues()`, `get_projects()`, `get_users()`
- [ ] Add methods: `create_issue()`, `update_issue()`, `transition_issue()`, `add_comment()`
- [ ] Implement pagination for search results
- [ ] Add retry logic with exponential backoff (3 retries)
- [ ] Add timeout configuration (default: 30s)
- [ ] Handle rate limiting (429 responses)
- [ ] Parse error responses and raise custom exceptions
- [ ] Write unit tests with httpx mock
- [ ] Write integration tests with mock Jira server

---

### Task 3.2: Implement Backfill Use Case
**Estimate**: 8 hours  
**Priority**: Critical  
**Dependencies**: Task 3.1, Task 2.2

**Description**: Implement initial data synchronization from Jira (backfill).

**Acceptance Criteria**:
- [ ] Create `src/application/use_cases/sync/backfill_instance.py`
- [ ] Fetch all projects from Jira instance
- [ ] Fetch all users from Jira instance
- [ ] Fetch all issues using JQL pagination (100 per page)
- [ ] Fetch comments for each issue
- [ ] Fetch changelogs for each issue
- [ ] Store data in database via repositories
- [ ] Handle duplicates (upsert logic)
- [ ] Update sync watermarks after completion
- [ ] Add progress logging (e.g., "Synced 500/1000 issues")
- [ ] Write integration tests with mock data
- [ ] Add error handling and rollback on failure

---

### Task 3.3: Implement Incremental Sync Use Case
**Estimate**: 6 hours  
**Priority**: Critical  
**Dependencies**: Task 3.1, Task 2.2

**Description**: Implement incremental synchronization via webhooks.

**Acceptance Criteria**:
- [ ] Create `src/application/use_cases/sync/sync_issue.py`
- [ ] Parse webhook payload (issue.updated, comment.created, etc.)
- [ ] Fetch updated issue from Jira API
- [ ] Upsert issue in database
- [ ] Fetch and upsert comments if changed
- [ ] Fetch and upsert changelogs if changed
- [ ] Update sync watermark
- [ ] Invalidate cache for updated issue
- [ ] Add idempotency (handle duplicate webhooks)
- [ ] Write unit tests with mock webhook payloads
- [ ] Write integration tests

---

### Task 3.4: Implement Polling Fallback
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 3.1, Task 2.2

**Description**: Implement polling-based sync for instances without webhooks.

**Acceptance Criteria**:
- [ ] Create `src/application/use_cases/sync/poll_updates.py`
- [ ] Query issues with `updated >= last_watermark` using JQL
- [ ] Fetch updated issues in batches (100 per page)
- [ ] Upsert issues in database
- [ ] Update watermark to latest `updated` timestamp
- [ ] Add configurable poll interval (default: 5 minutes)
- [ ] Write unit tests
- [ ] Write integration tests

---

### Task 3.5: Create Celery Tasks for Background Sync
**Estimate**: 5 hours  
**Priority**: Critical  
**Dependencies**: Task 3.2, Task 3.3, Task 3.4

**Description**: Create Celery tasks for asynchronous data synchronization.

**Acceptance Criteria**:
- [ ] Install Celery: `pip install celery[redis]`
- [ ] Create `src/infrastructure/queue/celery_app.py` with Celery configuration
- [ ] Create `src/infrastructure/queue/tasks/sync_tasks.py`
- [ ] Create task: `backfill_instance_task(instance_id)`
- [ ] Create task: `sync_issue_task(instance_id, issue_key)`
- [ ] Create task: `poll_updates_task(instance_id)`
- [ ] Add periodic task for polling (every 5 minutes)
- [ ] Add task retry logic (max 3 retries, exponential backoff)
- [ ] Add task timeout (5 minutes)
- [ ] Write tests for Celery tasks
- [ ] Document Celery setup in README

---

### Task 3.6: Implement Rate Limiting Per Instance
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 1.6, Task 3.1

**Description**: Implement token bucket rate limiting per Jira instance.

**Acceptance Criteria**:
- [ ] Create `src/application/services/rate_limit_service.py`
- [ ] Implement token bucket algorithm using Redis
- [ ] Configure rate limit: 100 requests per minute per instance
- [ ] Add rate limit check before Jira API calls
- [ ] Raise `RateLimitExceeded` exception when limit reached
- [ ] Add `Retry-After` header in response
- [ ] Add rate limit metrics (requests, tokens remaining)
- [ ] Write unit tests with fakeredis
- [ ] Write integration tests

---

### Task 3.7: Add Retry Logic with Exponential Backoff
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 3.1

**Description**: Add robust retry logic for transient failures.

**Acceptance Criteria**:
- [ ] Install `tenacity`: `pip install tenacity`
- [ ] Add `@retry` decorator to Jira API calls
- [ ] Configure retry: max 3 attempts, exponential backoff (1s, 2s, 4s)
- [ ] Retry on: connection errors, timeouts, 5xx responses
- [ ] Do NOT retry on: 4xx responses (except 429)
- [ ] Log retry attempts with context
- [ ] Add retry metrics
- [ ] Write tests for retry behavior

---

### Task 3.8: Create Reconciliation Job
**Estimate**: 4 hours  
**Priority**: Medium  
**Dependencies**: Task 3.1, Task 2.2

**Description**: Create periodic job to detect data drift between Jira and database.

**Acceptance Criteria**:
- [ ] Create `src/application/use_cases/sync/reconcile_data.py`
- [ ] Sample random 100 issues from database
- [ ] Fetch same issues from Jira API
- [ ] Compare `updated_at` timestamps
- [ ] Log discrepancies (drift detected)
- [ ] Trigger re-sync for drifted issues
- [ ] Create Celery periodic task (daily at 2 AM)
- [ ] Write unit tests
- [ ] Write integration tests

---

### Task 3.9: Write Integration Tests for Sync
**Estimate**: 6 hours  
**Priority**: High  
**Dependencies**: Task 3.2, Task 3.3, Task 3.4

**Description**: Comprehensive integration tests for sync layer.

**Acceptance Criteria**:
- [ ] Test backfill with mock Jira server (100 issues)
- [ ] Test incremental sync with webhook payloads
- [ ] Test polling fallback with updated issues
- [ ] Test rate limiting behavior
- [ ] Test retry logic with transient failures
- [ ] Test idempotency (duplicate webhooks)
- [ ] Test error handling and rollback
- [ ] Achieve 80%+ code coverage

---

## Phase 4: Application Layer (Week 7-8)

### Task 4.1: Create Use Cases for Issue Operations
**Estimate**: 8 hours  
**Priority**: Critical  
**Dependencies**: Task 2.2

**Description**: Implement business use cases for issue operations.

**Acceptance Criteria**:
- [ ] Create `src/application/use_cases/issues/create_issue.py`
- [ ] Create `src/application/use_cases/issues/update_issue.py`
- [ ] Create `src/application/use_cases/issues/transition_issue.py`
- [ ] Create `src/application/use_cases/issues/search_issues.py`
- [ ] Create `src/application/use_cases/issues/add_comment.py`
- [ ] Add validation logic (required fields, valid transitions)
- [ ] Add authorization checks (tenant isolation)
- [ ] Call Jira API client for write operations
- [ ] Update database via repositories
- [ ] Invalidate cache after writes
- [ ] Write unit tests for each use case (80%+ coverage)

---

### Task 4.2: Implement AI Use Cases
**Estimate**: 6 hours  
**Priority**: High  
**Dependencies**: Task 2.2

**Description**: Implement AI-powered use cases (intent classification, response generation, PII detection).

**Acceptance Criteria**:
- [ ] Create `src/application/use_cases/ai/classify_intent.py`
- [ ] Create `src/application/use_cases/ai/generate_response.py`
- [ ] Create `src/application/use_cases/ai/detect_pii.py`
- [ ] Integrate with AI provider (OpenAI, Anthropic, Google)
- [ ] Add prompt templates
- [ ] Add response parsing and validation
- [ ] Add cost tracking per AI call
- [ ] Add rate limiting per tenant
- [ ] Write unit tests with mocked AI responses

---

### Task 4.3: Create DTOs for API Boundaries
**Estimate**: 4 hours  
**Priority**: High  
**Dependencies**: Task 4.1

**Description**: Create Data Transfer Objects (DTOs) for API request/response.

**Acceptance Criteria**:
- [ ] Create `src/application/dtos/issue_dto.py` with IssueDTO, CreateIssueDTO, UpdateIssueDTO
- [ ] Create `src/application/dtos/search_dto.py` with SearchRequestDTO, SearchResponseDTO
- [ ] Create `src/application/dtos/metrics_dto.py` with MetricsDTO
- [ ] Add Pydantic models with validation
- [ ] Add type hints
- [ ] Add serialization methods (to_dict, from_dict)
- [ ] Write unit tests for DTO validation

---

### Task 4.4: Implement Application Services
**Estimate**: 5 hours  
**Priority**: High  
**Dependencies**: Task 2.2

**Description**: Implement cross-cutting application services (auth, tenant management).

**Acceptance Criteria**:
- [ ] Create `src/application/services/auth_service.py`
- [ ] Implement JWT token generation and validation
- [ ] Implement API key validation
- [ ] Create `src/application/services/tenant_service.py`
- [ ] Implement tenant CRUD operations
- [ ] Implement tenant context management (set current tenant)
- [ ] Write unit tests for services

---

### Task 4.5: Add Audit Logging for Write Operations
**Estimate**: 3 hours  
**Priority**: High  
**Dependencies**: Task 2.1

**Description**: Implement audit logging for all write operations.

**Acceptance Criteria**:
- [ ] Create `src/application/services/audit_service.py`
- [ ] Add `log_audit()` method with parameters: actor, action, target, payload
- [ ] Call audit service in all write use cases
- [ ] Store audit logs in `audit_log` table
- [ ] Add audit log query methods (by tenant, by actor, by date range)
- [ ] Write unit tests

---

### Task 4.6: Write Unit Tests for Use Cases
**Estimate**: 8 hours  
**Priority**: High  
**Dependencies**: Task 4.1, Task 4.2

**Description**: Comprehensive unit tests for all use cases.

**Acceptance Criteria**:
- [ ] Test create_issue use case with valid/invalid inputs
- [ ] Test update_issue use case with authorization checks
- [ ] Test transition_issue use case with valid/invalid transitions
- [ ] Test search_issues use case with various filters
- [ ] Test AI use cases with mocked AI responses
- [ ] Test error handling and exceptions
- [ ] Achieve 80%+ code coverage
- [ ] Use pytest fixtures and mocks

---

## Summary

**Total Tasks**: 40+  
**Estimated Duration**: 12 weeks  
**Critical Path**: Foundation → Data Layer → Sync Layer → Application Layer → REST API → MCP Interface → Migration

**Key Milestones**:
- Week 2: Foundation complete (database, models, entities)
- Week 4: Data layer complete (repositories, caching, RLS)
- Week 6: Sync layer complete (backfill, incremental, polling)
- Week 8: Application layer complete (use cases, DTOs, services)
- Week 10: REST API complete (routers, middleware, tests)
- Week 11: MCP interface complete
- Week 12: Migration complete, old code removed

**Next Steps**:
1. Review and approve this task breakdown
2. Assign tasks to team members
3. Set up project tracking (Jira, GitHub Projects, etc.)
4. Run `/implement` to start implementation

