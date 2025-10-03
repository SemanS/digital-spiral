# Technical Plan - MCP & SQL Enhancement

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Admin UI (Next.js)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Instances   │  │   Projects   │  │   Metrics    │          │
│  │  Management  │  │   Dashboard  │  │   Dashboard  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator (FastAPI)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Admin API (/api/v1/instances)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           AI Assistant API (/v1/ai-assistant)            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
         ┌──────────┴──────────┐    ┌──────────┴──────────┐
         │                     │    │                     │
         ▼                     ▼    ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   MCP Jira      │   │   MCP SQL       │   │  Source         │
│   Server        │   │   Server        │   │  Adapters       │
│   (SSE :8055)   │   │   (SSE :8056)   │   │  (Jira/GitHub)  │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                     │                     │
         └──────────┬──────────┴──────────┬──────────┘
                    │                     │
                    ▼                     ▼
         ┌─────────────────┐   ┌─────────────────┐
         │   PostgreSQL    │   │     Redis       │
         │   (RLS enabled) │   │   (Cache/RL)    │
         └─────────────────┘   └─────────────────┘
```

## 📦 Module Structure

```
digital-spiral/
├── src/
│   ├── interfaces/
│   │   ├── mcp/
│   │   │   ├── jira/
│   │   │   │   ├── server.py          # SSE server
│   │   │   │   ├── tools.py           # Tool implementations
│   │   │   │   ├── schemas.py         # Pydantic schemas
│   │   │   │   └── router.py          # FastAPI router
│   │   │   │
│   │   │   └── sql/
│   │   │       ├── server.py          # SSE server
│   │   │       ├── templates.py       # Query templates
│   │   │       ├── schemas.py         # Pydantic schemas
│   │   │       └── router.py          # FastAPI router
│   │   │
│   │   └── rest/
│   │       └── admin/
│   │           ├── instances.py       # Instance CRUD
│   │           ├── projects.py        # Project endpoints
│   │           └── sync.py            # Sync/backfill endpoints
│   │
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── mcp/
│   │   │   │   ├── execute_jira_tool.py
│   │   │   │   └── execute_sql_query.py
│   │   │   │
│   │   │   └── sync/
│   │   │       ├── sync_instance.py
│   │   │       └── backfill_instance.py
│   │   │
│   │   └── services/
│   │       ├── source_adapter_factory.py
│   │       ├── rate_limiter.py
│   │       └── idempotency_service.py
│   │
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── work_item.py
│   │   │   ├── source_instance.py
│   │   │   └── audit_log.py
│   │   │
│   │   └── services/
│   │       ├── status_normalizer.py
│   │       └── field_mapper.py
│   │
│   └── infrastructure/
│       ├── database/
│       │   ├── models/
│       │   │   ├── source_instance.py
│       │   │   ├── work_item.py
│       │   │   ├── audit_log.py
│       │   │   └── idempotency_key.py
│       │   │
│       │   ├── repositories/
│       │   │   ├── source_instance_repository.py
│       │   │   ├── work_item_repository.py
│       │   │   └── audit_log_repository.py
│       │   │
│       │   └── rls/
│       │       ├── policies.sql
│       │       └── context.py
│       │
│       ├── external/
│       │   ├── adapters/
│       │   │   ├── base.py            # SourceAdapter protocol
│       │   │   ├── jira_adapter.py
│       │   │   ├── github_adapter.py
│       │   │   └── asana_adapter.py
│       │   │
│       │   └── clients/
│       │       ├── jira_client.py
│       │       └── github_client.py
│       │
│       ├── cache/
│       │   ├── redis_cache.py
│       │   └── cache_keys.py
│       │
│       └── observability/
│           ├── metrics.py
│           ├── logging.py
│           └── tracing.py
│
├── migrations/
│   └── versions/
│       ├── xxx_add_source_instances.py
│       ├── xxx_add_work_items_indexes.py
│       ├── xxx_enable_rls.py
│       └── xxx_add_audit_log.py
│
└── tests/
    ├── unit/
    │   ├── mcp/
    │   ├── use_cases/
    │   └── domain/
    │
    ├── integration/
    │   ├── database/
    │   ├── cache/
    │   └── external/
    │
    └── e2e/
        ├── test_mcp_jira_flow.py
        ├── test_mcp_sql_flow.py
        └── test_multi_instance_flow.py
```

## 🔧 Implementation Details

### 1. MCP Jira Server

#### SSE Server (`src/interfaces/mcp/jira/server.py`)
```python
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import asyncio

app = FastAPI()

@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for MCP protocol."""
    async def event_generator():
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps({"server": "jira-mcp", "version": "1.0.0"})
        }
        
        # Heartbeat every 30s
        while True:
            if await request.is_disconnected():
                break
            yield {
                "event": "heartbeat",
                "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
            }
            await asyncio.sleep(30)
    
    return EventSourceResponse(event_generator())

@app.post("/tools/invoke")
async def invoke_tool(request: Request):
    """Invoke MCP tool (fallback to POST)."""
    body = await request.json()
    tool_name = body["name"]
    arguments = body.get("arguments", {})
    
    # Get tenant from auth
    tenant_id = get_tenant_from_auth(request)
    
    # Execute tool
    result = await execute_jira_tool(tool_name, arguments, tenant_id)
    return result
```

#### Tool Registry (`src/interfaces/mcp/jira/tools.py`)
```python
from typing import Dict, Callable, Any

TOOL_REGISTRY: Dict[str, Callable] = {}

def register_tool(name: str):
    """Decorator to register MCP tool."""
    def decorator(func: Callable):
        TOOL_REGISTRY[name] = func
        return func
    return decorator

@register_tool("jira.search")
async def jira_search(params: JiraSearchParams, context: MCPContext) -> JiraSearchResponse:
    """Search Jira issues."""
    # Validate params
    params = JiraSearchParams(**params)
    
    # Rate limit check
    await rate_limiter.check(context.instance_id)
    
    # Execute search
    adapter = get_adapter(context.instance_id)
    issues = await adapter.search(params.query, params.limit, params.cursor)
    
    # Audit log
    await audit_log.log("jira.search", context, params)
    
    return JiraSearchResponse(issues=issues, total=len(issues))
```

### 2. MCP SQL Server

#### Query Templates (`src/interfaces/mcp/sql/templates.py`)
```python
from typing import Dict
from sqlalchemy import text

QUERY_TEMPLATES: Dict[str, str] = {
    "search_issues_by_project": """
        SELECT * FROM work_items
        WHERE tenant_id = :tenant_id
          AND project_key = :project_key
          AND (:status IS NULL OR status = :status)
          AND (:assignee IS NULL OR assignee = :assignee)
        ORDER BY updated_at DESC
        LIMIT :limit
    """,
    
    "get_project_metrics": """
        SELECT * FROM work_item_metrics_daily
        WHERE tenant_id = :tenant_id
          AND project_key = :project_key
          AND date >= CURRENT_DATE - INTERVAL ':days days'
        ORDER BY date DESC
    """,
    
    # ... more templates
}

async def execute_template(
    template_name: str,
    params: Dict[str, Any],
    tenant_id: str
) -> List[Dict[str, Any]]:
    """Execute whitelisted SQL template."""
    if template_name not in QUERY_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
    
    # Validate params
    schema = TEMPLATE_SCHEMAS[template_name]
    validated_params = schema(**params)
    
    # Add tenant_id
    validated_params.tenant_id = tenant_id
    
    # Execute query
    async with get_session() as session:
        result = await session.execute(
            text(QUERY_TEMPLATES[template_name]),
            validated_params.dict()
        )
        return [dict(row) for row in result]
```

### 3. Source Adapters

#### Base Protocol (`src/infrastructure/external/adapters/base.py`)
```python
from typing import Protocol, List, Optional
from datetime import datetime

class SourceAdapter(Protocol):
    """Common interface for all PM systems."""
    
    async def search(
        self,
        query: str,
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> List[WorkItem]:
        """Search work items."""
        ...
    
    async def get_item(self, item_id: str) -> WorkItem:
        """Get single work item."""
        ...
    
    async def create_item(self, data: Dict[str, Any]) -> WorkItem:
        """Create new work item."""
        ...
    
    async def update_item(self, item_id: str, data: Dict[str, Any]) -> WorkItem:
        """Update work item."""
        ...
    
    async def list_projects(self) -> List[Project]:
        """List available projects."""
        ...
    
    async def sync_since(self, since: datetime) -> List[WorkItem]:
        """Sync items updated since timestamp."""
        ...
```

#### Jira Adapter (`src/infrastructure/external/adapters/jira_adapter.py`)
```python
class JiraAdapter:
    """Jira Cloud/Server adapter."""
    
    def __init__(self, instance: SourceInstance):
        self.instance = instance
        self.client = JiraClient(
            base_url=instance.base_url,
            credentials=decrypt_credentials(instance.encrypted_credentials)
        )
    
    async def search(self, query: str, limit: int, cursor: Optional[str]) -> List[WorkItem]:
        """Search Jira issues."""
        # Call Jira API
        response = await self.client.search(query, limit, cursor)
        
        # Convert to WorkItem
        items = [self._to_work_item(issue) for issue in response["issues"]]
        return items
    
    def _to_work_item(self, jira_issue: Dict) -> WorkItem:
        """Convert Jira issue to WorkItem."""
        return WorkItem(
            source="jira",
            source_id=jira_issue["id"],
            source_key=jira_issue["key"],
            instance_id=self.instance.id,
            project_key=jira_issue["fields"]["project"]["key"],
            title=jira_issue["fields"]["summary"],
            type=self._normalize_type(jira_issue["fields"]["issuetype"]["name"]),
            status=self._normalize_status(jira_issue["fields"]["status"]["name"]),
            priority=self._normalize_priority(jira_issue["fields"].get("priority")),
            assignee=jira_issue["fields"].get("assignee", {}).get("accountId"),
            reporter=jira_issue["fields"].get("reporter", {}).get("accountId"),
            created_at=parse_datetime(jira_issue["fields"]["created"]),
            updated_at=parse_datetime(jira_issue["fields"]["updated"]),
            custom_fields=self._extract_custom_fields(jira_issue["fields"]),
            raw_payload=jira_issue
        )
```

### 4. RLS Implementation

#### Enable RLS (`migrations/versions/xxx_enable_rls.py`)
```python
def upgrade():
    # Enable RLS on all tenant tables
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE source_instances ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE work_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE work_item_transitions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY")
    
    # Create policies
    op.execute("""
        CREATE POLICY tenant_isolation ON tenants
        FOR ALL
        USING (id = current_setting('app.current_tenant_id', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY instance_isolation ON source_instances
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    """)
    
    # ... more policies
```

#### Context Setup (`src/infrastructure/database/rls/context.py`)
```python
from contextvars import ContextVar
from sqlalchemy import event, text

current_tenant_id: ContextVar[Optional[UUID]] = ContextVar("current_tenant_id", default=None)

@event.listens_for(Engine, "begin")
def set_rls_context(conn):
    """Set RLS context at transaction begin."""
    tenant_id = current_tenant_id.get()
    if tenant_id:
        conn.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))

def set_tenant_context(tenant_id: UUID):
    """Set tenant context for current request."""
    current_tenant_id.set(tenant_id)

def clear_tenant_context():
    """Clear tenant context."""
    current_tenant_id.set(None)
```

### 5. Rate Limiting

#### Redis Token Bucket (`src/application/services/rate_limiter.py`)
```python
import redis.asyncio as redis
from datetime import datetime

class RateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check(self, instance_id: UUID, limit: int = 100, window: int = 60):
        """Check if request is allowed."""
        key = f"rate_limit:{instance_id}"
        
        # Get current count
        count = await self.redis.get(key)
        
        if count is None:
            # First request in window
            await self.redis.setex(key, window, 1)
            return True
        
        count = int(count)
        if count >= limit:
            # Rate limit exceeded
            ttl = await self.redis.ttl(key)
            raise RateLimitError(f"Rate limit exceeded", retry_after=ttl)
        
        # Increment counter
        await self.redis.incr(key)
        return True
```

### 6. Idempotency

#### Idempotency Service (`src/application/services/idempotency_service.py`)
```python
class IdempotencyService:
    """Handle idempotent write operations."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours
    
    async def check_and_store(
        self,
        idempotency_key: str,
        tenant_id: UUID,
        operation: str
    ) -> Optional[Dict[str, Any]]:
        """Check if operation was already executed."""
        key = f"idempotency:{tenant_id}:{operation}:{idempotency_key}"
        
        # Check if exists
        result = await self.redis.get(key)
        if result:
            return json.loads(result)
        
        return None
    
    async def store_result(
        self,
        idempotency_key: str,
        tenant_id: UUID,
        operation: str,
        result: Dict[str, Any]
    ):
        """Store operation result."""
        key = f"idempotency:{tenant_id}:{operation}:{idempotency_key}"
        await self.redis.setex(key, self.ttl, json.dumps(result))
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/mcp/test_jira_tools.py
async def test_jira_search_validates_params():
    with pytest.raises(ValidationError):
        await jira_search({"query": ""}, context)

async def test_jira_search_rate_limited():
    # Mock rate limiter to raise error
    with pytest.raises(RateLimitError):
        await jira_search(params, context)
```

### Integration Tests
```python
# tests/integration/database/test_rls.py
async def test_rls_isolates_tenants(db_session):
    # Create data for two tenants
    tenant1 = create_tenant()
    tenant2 = create_tenant()
    
    # Set context to tenant1
    set_tenant_context(tenant1.id)
    
    # Query should only return tenant1 data
    items = await work_item_repo.list_all()
    assert all(item.tenant_id == tenant1.id for item in items)
```

### E2E Tests
```python
# tests/e2e/test_mcp_jira_flow.py
async def test_full_mcp_jira_flow(client):
    # 1. Add instance
    response = await client.post("/api/v1/instances", json={...})
    instance_id = response.json()["instance"]["id"]
    
    # 2. Test connection
    response = await client.post(f"/api/v1/instances/{instance_id}/test")
    assert response.json()["connected"] == True
    
    # 3. Backfill
    response = await client.post(f"/api/v1/instances/{instance_id}/backfill")
    task_id = response.json()["task_id"]
    
    # 4. Wait for completion
    await wait_for_task(task_id)
    
    # 5. Query via SQL MCP
    response = await client.post("/mcp/sql/invoke", json={
        "name": "search_issues_by_project",
        "arguments": {"project_key": "PROJ", "tenant_id": "demo"}
    })
    assert len(response.json()["issues"]) > 0
```

## 📊 Observability

### Metrics
```python
# src/infrastructure/observability/metrics.py
from prometheus_client import Counter, Histogram

mcp_tool_calls = Counter(
    "mcp_tool_calls_total",
    "Total MCP tool calls",
    ["tool", "status"]
)

mcp_tool_duration = Histogram(
    "mcp_tool_duration_seconds",
    "MCP tool execution duration",
    ["tool"]
)

sql_query_duration = Histogram(
    "sql_query_duration_seconds",
    "SQL query execution duration",
    ["template"]
)
```

### Structured Logging
```python
# src/infrastructure/observability/logging.py
import structlog

logger = structlog.get_logger()

logger.info(
    "mcp_tool_executed",
    tool="jira.search",
    tenant_id=str(tenant_id),
    instance_id=str(instance_id),
    duration_ms=duration,
    status="success"
)
```

## 🚀 Deployment

### Docker Compose
```yaml
services:
  mcp-jira:
    build: .
    command: python -m src.interfaces.mcp.jira.server
    ports:
      - "8055:8055"
    environment:
      - DATABASE_URL
      - REDIS_URL
  
  mcp-sql:
    build: .
    command: python -m src.interfaces.mcp.sql.server
    ports:
      - "8056:8056"
```

---

**Version:** 1.0.0  
**Created:** 2025-10-03  
**Status:** Draft

