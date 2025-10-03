# Tasks - MCP & SQL Enhancement

## 📋 Task Breakdown

### Phase 1: Foundation & Data Models

#### 1.1 Database Models & Migrations
- [ ] **Task 1.1.1:** Create `source_instances` model
  - Fields: id, tenant_id, source_type, base_url, encrypted_credentials, auth_type, is_active, sync_enabled, last_sync_at
  - Relationships: work_items, projects, users
  - Migration: `migrations/versions/xxx_add_source_instances.py`
  - Tests: `tests/unit/database/models/test_source_instance.py`

- [ ] **Task 1.1.2:** Enhance `work_items` model for multi-source
  - Add: source, source_id, source_key, instance_id (FK)
  - Update: custom_fields (JSONB), raw_payload (JSONB)
  - Migration: `migrations/versions/xxx_enhance_work_items.py`
  - Tests: `tests/unit/database/models/test_work_item.py`

- [ ] **Task 1.1.3:** Create `audit_log` model
  - Fields: id, tenant_id, user_id, action, resource_type, resource_id, changes, timestamp
  - Indexes: tenant_id, timestamp, resource_type
  - Migration: `migrations/versions/xxx_add_audit_log.py`
  - Tests: `tests/unit/database/models/test_audit_log.py`

- [ ] **Task 1.1.4:** Create `idempotency_keys` model
  - Fields: id, tenant_id, key, operation, result, expires_at
  - Indexes: tenant_id + key (unique), expires_at
  - Migration: `migrations/versions/xxx_add_idempotency_keys.py`
  - Tests: `tests/unit/database/models/test_idempotency_key.py`

#### 1.2 Database Indexes & Performance
- [ ] **Task 1.2.1:** Add B-tree indexes
  - work_items: (tenant_id, project_key, status)
  - work_items: (tenant_id, assignee, status)
  - work_items: (tenant_id, instance_id, updated_at)
  - Migration: `migrations/versions/xxx_add_work_items_indexes.py`

- [ ] **Task 1.2.2:** Add GIN indexes for JSONB
  - work_items.custom_fields (GIN)
  - work_items.raw_payload (GIN)
  - Migration: `migrations/versions/xxx_add_jsonb_indexes.py`

- [ ] **Task 1.2.3:** Add trigram index for full-text search
  - work_items.title (GIN with pg_trgm)
  - Requires: CREATE EXTENSION pg_trgm
  - Migration: `migrations/versions/xxx_add_trgm_index.py`

- [ ] **Task 1.2.4:** Create EXPLAIN ANALYZE test suite
  - Test all SQL templates with EXPLAIN (ANALYZE, BUFFERS)
  - Document query plans
  - File: `tests/performance/test_query_plans.py`

#### 1.3 Row-Level Security (RLS)
- [ ] **Task 1.3.1:** Enable RLS on all tenant tables
  - Tables: tenants, source_instances, work_items, work_item_transitions, audit_log
  - Migration: `migrations/versions/xxx_enable_rls.py`

- [ ] **Task 1.3.2:** Create RLS policies
  - SELECT policies for all tables
  - INSERT/UPDATE/DELETE policies with WITH CHECK
  - File: `src/infrastructure/database/rls/policies.sql`

- [ ] **Task 1.3.3:** Implement RLS context management
  - ContextVar for current_tenant_id
  - SQLAlchemy event listener for SET LOCAL
  - File: `src/infrastructure/database/rls/context.py`
  - Tests: `tests/integration/database/test_rls.py`

### Phase 2: MCP Jira Implementation

#### 2.1 Pydantic Schemas
- [ ] **Task 2.1.1:** Define input schemas for all tools
  - JiraSearchParams, JiraGetIssueParams, JiraCreateIssueParams, etc.
  - Validators for JQL, issue keys, ADF format
  - File: `src/interfaces/mcp/jira/schemas.py`
  - Tests: `tests/unit/mcp/jira/test_schemas.py`

- [ ] **Task 2.1.2:** Define output schemas
  - JiraSearchResponse, JiraIssueResponse, etc.
  - Include metadata: query_time_ms, instance_id
  - File: `src/interfaces/mcp/jira/schemas.py`

- [ ] **Task 2.1.3:** Define error schemas
  - MCPError with code, message, details, retry_after
  - Error code enum: validation_error, rate_limited, etc.
  - File: `src/interfaces/mcp/jira/errors.py`

#### 2.2 SSE Server
- [ ] **Task 2.2.1:** Implement SSE endpoint
  - GET /sse with EventSourceResponse
  - Connection event, heartbeat (30s)
  - Authentication via Bearer token
  - File: `src/interfaces/mcp/jira/server.py`
  - Tests: `tests/integration/mcp/jira/test_sse.py`

- [ ] **Task 2.2.2:** Implement POST /tools/invoke endpoint
  - Fallback for non-SSE clients
  - Request: {name, arguments}
  - Response: tool result or error
  - File: `src/interfaces/mcp/jira/router.py`

#### 2.3 Tool Implementations
- [ ] **Task 2.3.1:** Implement jira.search
  - Multi-instance support (instance_id optional)
  - Pagination with cursor
  - Rate limiting check
  - Audit logging
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_search.py`

- [ ] **Task 2.3.2:** Implement jira.get_issue
  - Auto-detect instance from issue_key
  - Expand support (changelog, comments)
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_get_issue.py`

- [ ] **Task 2.3.3:** Implement jira.create_issue
  - Idempotency key support
  - ADF validation
  - Audit log creation
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_create_issue.py`

- [ ] **Task 2.3.4:** Implement jira.update_issue
  - Idempotency key support
  - Field validation
  - Audit log creation
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_update_issue.py`

- [ ] **Task 2.3.5:** Implement jira.transition_issue
  - Status name to transition ID mapping
  - Optional comment support
  - Idempotency key support
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_transition_issue.py`

- [ ] **Task 2.3.6:** Implement jira.add_comment
  - ADF format validation
  - Visibility restrictions support
  - Idempotency key support
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_add_comment.py`

- [ ] **Task 2.3.7:** Implement jira.link_issues
  - Link type validation
  - Cross-instance linking support
  - Idempotency key support
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_link_issues.py`

- [ ] **Task 2.3.8:** Implement jira.list_transitions
  - Get available transitions for issue
  - File: `src/interfaces/mcp/jira/tools.py`
  - Tests: `tests/unit/mcp/jira/test_list_transitions.py`

#### 2.4 Audit Log & Idempotency
- [ ] **Task 2.4.1:** Implement audit log service
  - Log all write operations
  - Include: user_id, action, resource, changes, timestamp
  - File: `src/application/services/audit_log_service.py`
  - Tests: `tests/unit/services/test_audit_log_service.py`

- [ ] **Task 2.4.2:** Implement idempotency service
  - Redis-based storage (24h TTL)
  - Check and store results
  - File: `src/application/services/idempotency_service.py`
  - Tests: `tests/unit/services/test_idempotency_service.py`

#### 2.5 Rate Limiting
- [ ] **Task 2.5.1:** Implement rate limiter
  - Redis token bucket algorithm
  - Per-instance limits (100 rpm default)
  - Retry-After header on 429
  - File: `src/application/services/rate_limiter.py`
  - Tests: `tests/unit/services/test_rate_limiter.py`

- [ ] **Task 2.5.2:** Integrate rate limiter with tools
  - Check before each tool execution
  - Return rate_limited error with retry_after
  - Tests: `tests/integration/mcp/jira/test_rate_limiting.py`

### Phase 3: MCP SQL Implementation

#### 3.1 Query Templates
- [ ] **Task 3.1.1:** Define search_issues_by_project template
  - Parameters: project_key, status, assignee, priority, limit
  - SQL with proper indexes
  - File: `src/interfaces/mcp/sql/templates.py`
  - Tests: `tests/unit/mcp/sql/test_search_issues_by_project.py`

- [ ] **Task 3.1.2:** Define get_project_metrics template
  - Parameters: project_key, days
  - Use materialized view
  - File: `src/interfaces/mcp/sql/templates.py`
  - Tests: `tests/unit/mcp/sql/test_get_project_metrics.py`

- [ ] **Task 3.1.3:** Define search_issues_by_text template
  - Parameters: query, project_keys, limit
  - Use trigram similarity
  - File: `src/interfaces/mcp/sql/templates.py`
  - Tests: `tests/unit/mcp/sql/test_search_issues_by_text.py`

- [ ] **Task 3.1.4:** Define get_issue_history template
  - Parameters: issue_key
  - Join work_items + work_item_transitions
  - File: `src/interfaces/mcp/sql/templates.py`
  - Tests: `tests/unit/mcp/sql/test_get_issue_history.py`

- [ ] **Task 3.1.5:** Define get_user_workload template
  - Parameters: assignee, status
  - Aggregate by project_key
  - File: `src/interfaces/mcp/sql/templates.py`
  - Tests: `tests/unit/mcp/sql/test_get_user_workload.py`

- [ ] **Task 3.1.6:** Define lead_time_metrics template
  - Parameters: project_key, team, days
  - Use metrics materialized view
  - File: `src/interfaces/mcp/sql/templates.py`
  - Tests: `tests/unit/mcp/sql/test_lead_time_metrics.py`

#### 3.2 Parameter Validation
- [ ] **Task 3.2.1:** Create Pydantic schemas for all templates
  - Type checking, range validation
  - Array length limits
  - File: `src/interfaces/mcp/sql/schemas.py`
  - Tests: `tests/unit/mcp/sql/test_schemas.py`

- [ ] **Task 3.2.2:** Implement SQL injection protection
  - Parameterized queries only
  - No raw SQL from user input
  - Whitelist validation
  - Tests: `tests/security/test_sql_injection.py`

#### 3.3 SSE Server
- [ ] **Task 3.3.1:** Implement SSE endpoint for SQL MCP
  - Similar to Jira MCP
  - Port 8056
  - File: `src/interfaces/mcp/sql/server.py`
  - Tests: `tests/integration/mcp/sql/test_sse.py`

- [ ] **Task 3.3.2:** Implement POST /query endpoint
  - Request: {template_name, params}
  - Response: query results
  - File: `src/interfaces/mcp/sql/router.py`

#### 3.4 Performance Monitoring
- [ ] **Task 3.4.1:** Add query execution metrics
  - Histogram for query duration
  - Counter for query executions
  - File: `src/infrastructure/observability/metrics.py`

- [ ] **Task 3.4.2:** Implement slow query logging
  - Log queries > 100ms
  - Include query plan
  - File: `src/infrastructure/observability/logging.py`

### Phase 4: Multi-Source Support

#### 4.1 Source Adapter Interface
- [ ] **Task 4.1.1:** Define SourceAdapter protocol
  - Methods: search, get_item, create_item, update_item, list_projects, sync_since
  - File: `src/infrastructure/external/adapters/base.py`
  - Tests: `tests/unit/adapters/test_base.py`

- [ ] **Task 4.1.2:** Implement JiraAdapter
  - Implement all protocol methods
  - Convert Jira responses to WorkItem
  - File: `src/infrastructure/external/adapters/jira_adapter.py`
  - Tests: `tests/unit/adapters/test_jira_adapter.py`

- [ ] **Task 4.1.3:** Implement GitHubAdapter (basic)
  - Support for GitHub Issues + PRs
  - Convert to WorkItem format
  - File: `src/infrastructure/external/adapters/github_adapter.py`
  - Tests: `tests/unit/adapters/test_github_adapter.py`

- [ ] **Task 4.1.4:** Implement AsanaAdapter (basic)
  - Support for Asana tasks
  - Convert to WorkItem format
  - File: `src/infrastructure/external/adapters/asana_adapter.py`
  - Tests: `tests/unit/adapters/test_asana_adapter.py`

#### 4.2 Status & Field Normalization
- [ ] **Task 4.2.1:** Implement status normalizer
  - Mapping tables for each source
  - Normalize to: open, in_progress, done, closed
  - File: `src/domain/services/status_normalizer.py`
  - Tests: `tests/unit/domain/test_status_normalizer.py`

- [ ] **Task 4.2.2:** Implement field mapper
  - Map source-specific fields to WorkItem
  - Handle custom fields (JSONB)
  - File: `src/domain/services/field_mapper.py`
  - Tests: `tests/unit/domain/test_field_mapper.py`

#### 4.3 Adapter Factory
- [ ] **Task 4.3.1:** Implement SourceAdapterFactory
  - Create adapter based on source_type
  - Dependency injection for clients
  - File: `src/application/services/source_adapter_factory.py`
  - Tests: `tests/unit/services/test_source_adapter_factory.py`

### Phase 5: Admin API & UI

#### 5.1 REST Endpoints
- [ ] **Task 5.1.1:** Implement GET /api/v1/instances
  - List all instances for tenant
  - Include status, last_sync
  - File: `src/interfaces/rest/admin/instances.py`
  - Tests: `tests/integration/rest/test_instances_list.py`

- [ ] **Task 5.1.2:** Implement GET /api/v1/instances/:id
  - Get single instance details
  - File: `src/interfaces/rest/admin/instances.py`
  - Tests: `tests/integration/rest/test_instances_get.py`

- [ ] **Task 5.1.3:** Implement POST /api/v1/instances
  - Create new instance
  - Encrypt credentials
  - File: `src/interfaces/rest/admin/instances.py`
  - Tests: `tests/integration/rest/test_instances_create.py`

- [ ] **Task 5.1.4:** Implement PATCH /api/v1/instances/:id
  - Update instance configuration
  - Re-encrypt credentials if changed
  - File: `src/interfaces/rest/admin/instances.py`
  - Tests: `tests/integration/rest/test_instances_update.py`

- [ ] **Task 5.1.5:** Implement DELETE /api/v1/instances/:id
  - Soft delete instance
  - Cascade to work_items (soft delete)
  - File: `src/interfaces/rest/admin/instances.py`
  - Tests: `tests/integration/rest/test_instances_delete.py`

- [ ] **Task 5.1.6:** Implement POST /api/v1/instances/:id/test
  - Test connection to source
  - Return connected status + error
  - File: `src/interfaces/rest/admin/instances.py`
  - Tests: `tests/integration/rest/test_instances_test.py`

- [ ] **Task 5.1.7:** Implement POST /api/v1/instances/:id/backfill
  - Trigger backfill task (Celery)
  - Return task_id
  - File: `src/interfaces/rest/admin/sync.py`
  - Tests: `tests/integration/rest/test_backfill.py`

- [ ] **Task 5.1.8:** Implement GET /api/v1/instances/:id/backfill/:task_id
  - Get backfill task status
  - Return: status, progress, error
  - File: `src/interfaces/rest/admin/sync.py`
  - Tests: `tests/integration/rest/test_backfill_status.py`

#### 5.2 Admin UI (Next.js)
- [ ] **Task 5.2.1:** Create instance list page
  - Table with name, source, status, last_sync
  - Actions: Edit, Test, Backfill, Delete
  - File: `admin-ui/src/app/instances/page.tsx`

- [ ] **Task 5.2.2:** Create add instance wizard
  - Step 1: Select source (Jira, GitHub, Asana)
  - Step 2: Connection details
  - Step 3: Test connection
  - Step 4: Configure sync
  - Step 5: Save & backfill
  - File: `admin-ui/src/app/instances/new/page.tsx`

- [ ] **Task 5.2.3:** Create instance detail page
  - Show configuration
  - Sync history
  - Actions: Edit, Test, Backfill
  - File: `admin-ui/src/app/instances/[id]/page.tsx`

### Phase 6: Observability & QA

#### 6.1 Metrics
- [ ] **Task 6.1.1:** Implement Prometheus metrics
  - MCP tool calls (counter, histogram)
  - SQL queries (counter, histogram)
  - Sync operations (counter, histogram)
  - File: `src/infrastructure/observability/metrics.py`

- [ ] **Task 6.1.2:** Add /metrics endpoint
  - Expose Prometheus metrics
  - File: `src/interfaces/rest/metrics.py`

#### 6.2 Logging
- [ ] **Task 6.2.1:** Implement structured logging
  - JSON format with tenant_id, user_id, instance_id
  - Log levels: DEBUG, INFO, WARNING, ERROR
  - File: `src/infrastructure/observability/logging.py`

#### 6.3 Tracing
- [ ] **Task 6.3.1:** Implement OpenTelemetry tracing
  - Trace MCP tool calls
  - Trace SQL queries
  - Propagate traceparent
  - File: `src/infrastructure/observability/tracing.py`

#### 6.4 E2E Tests
- [ ] **Task 6.4.1:** E2E test: Add Jira instance → backfill → query
  - Full flow from UI to database
  - File: `tests/e2e/test_jira_instance_flow.py`

- [ ] **Task 6.4.2:** E2E test: Multi-instance SQL queries
  - Query across multiple instances
  - Verify data isolation
  - File: `tests/e2e/test_multi_instance_queries.py`

- [ ] **Task 6.4.3:** E2E test: Cross-source aggregation
  - Combine Jira + GitHub data
  - Verify normalization
  - File: `tests/e2e/test_cross_source_aggregation.py`

---

**Total Tasks:** 100+  
**Estimated Effort:** 8-12 weeks  
**Version:** 1.0.0  
**Created:** 2025-10-03  
**Status:** Draft

