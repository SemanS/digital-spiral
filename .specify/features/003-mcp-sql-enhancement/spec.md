# Specification - MCP & SQL Enhancement

## 🎯 Overview

Rozšírenie existujúceho MCP a SQL systému pre plnohodnotné multi-source manažérske rozhodovanie. Umožní kombinovať informácie z viacerých Jira inštancií, GitHub, Asana, Linear a ďalších PM nástrojov cez jednotné MCP a SQL rozhranie.

## 🔧 MCP (Jira) Enhancement

### Nástroje (Tools)

#### 1. `jira.search`
**Popis:** Vyhľadávanie issues pomocou JQL s podporou multi-instance.

**Parametre:**
```typescript
{
  query: string;              // JQL query
  instance_id?: UUID;         // Specific instance (optional, default: all)
  limit?: number;             // Max results (default: 50, max: 100)
  cursor?: string;            // Pagination cursor
  fields?: string[];          // Fields to return (default: summary, status, assignee)
}
```

**Response:**
```typescript
{
  issues: Issue[];
  total: number;
  cursor?: string;            // Next page cursor
  instance_id: UUID;
}
```

#### 2. `jira.get_issue`
**Popis:** Získanie detailu konkrétneho issue.

**Parametre:**
```typescript
{
  issue_key: string;          // PROJ-123
  instance_id?: UUID;         // Auto-detect if not provided
}
```

#### 3. `jira.create_issue`
**Popis:** Vytvorenie nového issue s audit logom.

**Parametre:**
```typescript
{
  instance_id: UUID;
  project_key: string;
  issue_type_id: string;
  summary: string;
  description_adf?: object;   // Atlassian Document Format
  fields?: object;            // Custom fields
  idempotency_key?: string;   // For retry safety
}
```

#### 4. `jira.update_issue`
**Popis:** Aktualizácia existujúceho issue.

**Parametre:**
```typescript
{
  issue_key: string;
  instance_id?: UUID;
  fields: object;             // Fields to update
  idempotency_key?: string;
}
```

#### 5. `jira.list_transitions`
**Popis:** Zoznam dostupných prechodov pre issue.

**Parametre:**
```typescript
{
  issue_key: string;
  instance_id?: UUID;
}
```

#### 6. `jira.transition_issue`
**Popis:** Zmena statusu issue.

**Parametre:**
```typescript
{
  issue_key: string;
  to_status: string;          // Target status name
  instance_id?: UUID;
  comment?: string;           // Optional transition comment
  idempotency_key?: string;
}
```

#### 7. `jira.add_comment`
**Popis:** Pridanie komentára k issue.

**Parametre:**
```typescript
{
  issue_key: string;
  body_adf: object;           // Comment in ADF format
  instance_id?: UUID;
  idempotency_key?: string;
}
```

#### 8. `jira.link_issues`
**Popis:** Prepojenie dvoch issues.

**Parametre:**
```typescript
{
  inward_issue: string;       // PROJ-123
  outward_issue: string;      // PROJ-456
  link_type: string;          // "blocks", "relates to", etc.
  instance_id?: UUID;
  idempotency_key?: string;
}
```

### Bezpečnosť

#### Autorizácia
- **Per-tenant checks** - každý request validuje tenant_id
- **Instance ownership** - user môže pristupovať iba k svojim inštanciám
- **Rate limiting** - 100 rpm per instance (Redis token bucket)
- **Audit log** - všetky write operácie logované

#### Idempotencia
- **Idempotency keys** - write operácie s optional key
- **Deduplication window** - 24 hodín
- **Storage** - Redis s TTL

#### Error Handling
```typescript
type MCPError = {
  code: "validation_error" | "rate_limited" | "upstream_4xx" | "upstream_5xx" | "conflict" | "not_found" | "unauthorized";
  message: string;
  details?: object;
  retry_after?: number;       // For rate_limited
}
```

### Transport

#### SSE Endpoint
- **URL:** `http://localhost:8055/sse`
- **Production:** Cez reverse proxy (nginx/traefik)
- **Authentication:** Bearer token v Authorization header
- **Heartbeat:** Každých 30s

#### POST Endpoint (fallback)
- **URL:** `http://localhost:8055/tools/invoke`
- **Method:** POST
- **Body:** `{ name: string, arguments: object }`

## 🗄️ MCP (SQL) Enhancement

### Whitelisted Query Templates

#### 1. `search_issues_by_project`
**Popis:** Vyhľadávanie issues v projekte s filtrami.

**Parametre:**
```typescript
{
  project_key: string;
  status?: string;
  assignee?: string;
  priority?: string;
  limit?: number;             // Default: 50, max: 100
  tenant_id: string;
}
```

**SQL Template:**
```sql
SELECT * FROM work_items
WHERE tenant_id = :tenant_id
  AND project_key = :project_key
  AND (:status IS NULL OR status = :status)
  AND (:assignee IS NULL OR assignee = :assignee)
  AND (:priority IS NULL OR priority = :priority)
ORDER BY updated_at DESC
LIMIT :limit;
```

#### 2. `get_project_metrics`
**Popis:** Agregované metriky projektu za posledných N dní.

**Parametre:**
```typescript
{
  project_key: string;
  days: number;               // Default: 30, max: 365
  tenant_id: string;
}
```

**SQL Template:**
```sql
SELECT
  date,
  created,
  closed,
  wip,
  lead_time_p50_days,
  lead_time_p90_days
FROM work_item_metrics_daily
WHERE tenant_id = :tenant_id
  AND project_key = :project_key
  AND date >= CURRENT_DATE - INTERVAL ':days days'
ORDER BY date DESC;
```

#### 3. `search_issues_by_text`
**Popis:** Full-text search v issues (trigram matching).

**Parametre:**
```typescript
{
  query: string;
  project_keys: string[];     // Multi-project support
  limit?: number;             // Default: 20, max: 100
  tenant_id: string;
}
```

**SQL Template:**
```sql
SELECT * FROM work_items
WHERE tenant_id = :tenant_id
  AND project_key = ANY(:project_keys)
  AND title % :query         -- Trigram similarity
ORDER BY similarity(title, :query) DESC
LIMIT :limit;
```

#### 4. `get_issue_history`
**Popis:** História zmien pre konkrétne issue.

**Parametre:**
```typescript
{
  issue_key: string;
  tenant_id: string;
}
```

#### 5. `get_user_workload`
**Popis:** Workload používateľa naprieč projektami.

**Parametre:**
```typescript
{
  assignee: string;
  status?: string[];          // Filter by statuses
  tenant_id: string;
}
```

#### 6. `lead_time_metrics`
**Popis:** Lead time metriky pre projekt/team.

**Parametre:**
```typescript
{
  project_key?: string;
  team?: string;
  days: number;
  tenant_id: string;
}
```

### SQL Safety

#### Validácia
- **Pydantic schemas** pre všetky parametre
- **Type checking** - string, int, UUID, enum
- **Range validation** - min/max values
- **Array length limits** - max 50 items

#### Query Limits
- **Max rows:** 1000 per query
- **Timeout:** 30s statement_timeout
- **Complexity:** Max 5 JOINs
- **No raw SQL** - iba whitelisted templates

#### Performance Monitoring
- **EXPLAIN ANALYZE** v test mode
- **Slow query log** - queries > 100ms
- **Query plan cache** - PostgreSQL prepared statements

### Transport

#### SSE Endpoint
- **URL:** `http://localhost:8056/sse`
- **Same auth/heartbeat** ako Jira MCP

## 🗃️ Multi-Source Unification

### WorkItem Superset Model

```python
class WorkItem(Base):
    """Unified work item - superset naprieč všetkými PM systémami."""
    
    # Source identification
    source: str                 # jira | github | asana | linear | clickup
    source_id: str              # Original ID
    source_key: str             # PROJ-123, #456, etc.
    instance_id: UUID           # FK to source_instances
    
    # Common fields (normalized)
    project_key: str
    title: str
    type: str                   # bug | task | story | epic | issue | pr
    priority: str               # critical | high | medium | low
    status: str                 # Normalized: open | in_progress | done | closed
    
    # People
    assignee: str
    reporter: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    
    # Source-specific fields (JSONB)
    custom_fields: dict         # Source-specific data
    raw_payload: dict           # Full original response
```

### Source Adapters

#### Interface
```python
class SourceAdapter(Protocol):
    """Common interface pre všetky PM systémy."""
    
    async def search(self, query: str, **filters) -> list[WorkItem]: ...
    async def get_item(self, item_id: str) -> WorkItem: ...
    async def create_item(self, data: dict) -> WorkItem: ...
    async def update_item(self, item_id: str, data: dict) -> WorkItem: ...
    async def list_projects(self) -> list[Project]: ...
```

#### Implementations
- `JiraAdapter` - Jira Cloud/Server
- `GitHubAdapter` - GitHub Issues + PRs
- `AsanaAdapter` - Asana tasks
- `LinearAdapter` - Linear issues
- `ClickUpAdapter` - ClickUp tasks (future)

### Status Normalization

```python
STATUS_MAPPING = {
    "jira": {
        "To Do": "open",
        "In Progress": "in_progress",
        "Done": "done",
        "Closed": "closed",
    },
    "github": {
        "open": "open",
        "in_progress": "in_progress",
        "closed": "closed",
    },
    "asana": {
        "Not Started": "open",
        "In Progress": "in_progress",
        "Complete": "done",
    },
}
```

## 🔐 Row-Level Security (RLS)

### Politiky

#### tenants table
```sql
CREATE POLICY tenant_isolation ON tenants
  USING (id = current_setting('app.current_tenant_id')::uuid);
```

#### jira_instances table
```sql
CREATE POLICY instance_isolation ON jira_instances
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

#### work_items table
```sql
CREATE POLICY work_item_isolation ON work_items
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### Session Setup
```python
@event.listens_for(Engine, "connect")
def set_tenant_context(dbapi_conn, connection_record):
    """Set tenant context for RLS."""
    tenant_id = get_current_tenant_id()  # From request context
    with dbapi_conn.cursor() as cursor:
        cursor.execute(f"SET app.current_tenant_id = '{tenant_id}'")
```

## 🎨 Admin UI

### Instance Management

#### Add Instance Wizard
1. **Select Source** - Jira, GitHub, Asana, Linear
2. **Connection Details** - URL, credentials
3. **Test Connection** - Validate credentials
4. **Configure Sync** - Projects, sync interval
5. **Save & Backfill** - Initial data load

#### Instance List
- **Table view** - name, source, status, last_sync
- **Actions** - Edit, Test, Backfill, Delete
- **Status indicators** - Connected, Syncing, Error

### REST Endpoints

```typescript
// List instances
GET /api/v1/instances
Response: { instances: Instance[] }

// Get instance
GET /api/v1/instances/:id
Response: { instance: Instance }

// Create instance
POST /api/v1/instances
Body: { source, base_url, credentials, ... }
Response: { instance: Instance }

// Update instance
PATCH /api/v1/instances/:id
Body: { ... }
Response: { instance: Instance }

// Delete instance
DELETE /api/v1/instances/:id
Response: { success: boolean }

// Test connection
POST /api/v1/instances/:id/test
Response: { connected: boolean, error?: string }

// Trigger backfill
POST /api/v1/instances/:id/backfill
Body: { project_keys?: string[] }
Response: { task_id: string }

// Get backfill status
GET /api/v1/instances/:id/backfill/:task_id
Response: { status: "pending" | "running" | "completed" | "failed", progress: number }
```

## 📊 Telemetry

### Metrics (Prometheus)

```python
# MCP tool calls
mcp_tool_calls_total = Counter("mcp_tool_calls_total", ["tool", "status"])
mcp_tool_duration_seconds = Histogram("mcp_tool_duration_seconds", ["tool"])

# SQL queries
sql_query_total = Counter("sql_query_total", ["template", "status"])
sql_query_duration_seconds = Histogram("sql_query_duration_seconds", ["template"])

# Sync operations
sync_operations_total = Counter("sync_operations_total", ["source", "status"])
sync_duration_seconds = Histogram("sync_duration_seconds", ["source"])
```

### Structured Logs

```json
{
  "timestamp": "2025-10-03T10:30:00Z",
  "level": "info",
  "message": "MCP tool executed",
  "tenant_id": "uuid",
  "user_id": "uuid",
  "instance_id": "uuid",
  "tool": "jira.search",
  "duration_ms": 150,
  "status": "success"
}
```

## ✅ Definition of Done

### MCP Jira
- [ ] Všetky 8 nástrojov implementované
- [ ] SSE endpoint funkčný
- [ ] Audit log pre write operácie
- [ ] Rate limiting implementovaný
- [ ] Idempotency keys podporované
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests

### MCP SQL
- [ ] 6 query templates implementovaných
- [ ] Parameterizácia a validácia
- [ ] EXPLAIN ANALYZE testy
- [ ] Performance monitoring
- [ ] SSE endpoint funkčný
- [ ] Unit tests

### Multi-Source
- [ ] WorkItem superset model
- [ ] Jira adapter
- [ ] GitHub adapter (basic)
- [ ] Status normalization
- [ ] Source-agnostic queries

### RLS & Security
- [ ] RLS enabled na všetkých tabuľkách
- [ ] Politiky otestované
- [ ] Session context setup
- [ ] Integration tests pre izoláciu

### Admin UI
- [ ] Add instance wizard
- [ ] Instance list/detail
- [ ] Test connection
- [ ] Backfill trigger
- [ ] Status monitoring

### E2E Flow
- [ ] Pridať inštanciu → test → save
- [ ] Backfill → SQL queries fungujú
- [ ] Multi-instance queries
- [ ] Cross-source aggregation

---

**Version:** 1.0.0  
**Created:** 2025-10-03  
**Status:** Draft

