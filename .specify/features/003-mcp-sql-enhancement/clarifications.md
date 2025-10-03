# Clarifications - MCP & SQL Enhancement

## 🔍 MCP Tool Schemas (Detailed)

### 1. jira.search

#### Input Schema (Pydantic)
```python
class JiraSearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="JQL query string")
    instance_id: Optional[UUID] = Field(None, description="Specific Jira instance (None = all instances)")
    limit: int = Field(50, ge=1, le=100, description="Maximum results per page")
    cursor: Optional[str] = Field(None, description="Pagination cursor from previous response")
    fields: List[str] = Field(
        default=["summary", "status", "assignee", "priority"],
        max_items=50,
        description="Fields to include in response"
    )
    
    @validator("query")
    def validate_jql(cls, v):
        # Basic JQL validation
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
        if any(word in v.upper() for word in forbidden):
            raise ValueError("Invalid JQL query")
        return v
```

#### Output Schema
```python
class JiraSearchResponse(BaseModel):
    issues: List[Issue]
    total: int
    cursor: Optional[str]
    instance_id: UUID
    query_time_ms: int
```

#### Error Codes
- `validation_error` - Invalid JQL or parameters
- `rate_limited` - Rate limit exceeded (429)
- `upstream_4xx` - Jira API error (400-499)
- `upstream_5xx` - Jira server error (500-599)
- `not_found` - Instance not found
- `unauthorized` - Invalid credentials

### 2. jira.get_issue

#### Input Schema
```python
class JiraGetIssueParams(BaseModel):
    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$", description="Issue key (e.g., PROJ-123)")
    instance_id: Optional[UUID] = Field(None, description="Auto-detect if not provided")
    expand: List[str] = Field(
        default=["changelog", "comments"],
        max_items=10,
        description="Additional data to expand"
    )
```

#### Output Schema
```python
class JiraIssueResponse(BaseModel):
    issue: Issue
    instance_id: UUID
    query_time_ms: int
```

### 3. jira.create_issue

#### Input Schema
```python
class JiraCreateIssueParams(BaseModel):
    instance_id: UUID = Field(..., description="Target Jira instance")
    project_key: str = Field(..., regex=r"^[A-Z]+$", description="Project key")
    issue_type_id: str = Field(..., description="Issue type ID (e.g., '10001')")
    summary: str = Field(..., min_length=1, max_length=255, description="Issue summary")
    description_adf: Optional[Dict[str, Any]] = Field(None, description="Description in ADF format")
    fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom fields")
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    
    @validator("fields")
    def validate_fields(cls, v):
        # Limit custom fields
        if len(v) > 50:
            raise ValueError("Maximum 50 custom fields allowed")
        return v
```

#### Output Schema
```python
class JiraCreateIssueResponse(BaseModel):
    issue: Issue
    instance_id: UUID
    idempotency_key: Optional[str]
    audit_log_id: UUID
```

### 4. jira.update_issue

#### Input Schema
```python
class JiraUpdateIssueParams(BaseModel):
    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    instance_id: Optional[UUID] = None
    fields: Dict[str, Any] = Field(..., min_items=1, max_items=50)
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    notify_users: bool = Field(True, description="Send notifications")
```

### 5. jira.transition_issue

#### Input Schema
```python
class JiraTransitionIssueParams(BaseModel):
    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    to_status: str = Field(..., min_length=1, max_length=100, description="Target status name")
    instance_id: Optional[UUID] = None
    comment: Optional[str] = Field(None, max_length=5000, description="Transition comment")
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Fields to update during transition")
```

### 6. jira.add_comment

#### Input Schema
```python
class JiraAddCommentParams(BaseModel):
    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    body_adf: Dict[str, Any] = Field(..., description="Comment body in ADF format")
    instance_id: Optional[UUID] = None
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    visibility: Optional[Dict[str, str]] = Field(None, description="Comment visibility restrictions")
    
    @validator("body_adf")
    def validate_adf(cls, v):
        # Basic ADF validation
        if not isinstance(v, dict):
            raise ValueError("body_adf must be a dictionary")
        if v.get("version") != 1:
            raise ValueError("ADF version must be 1")
        if v.get("type") != "doc":
            raise ValueError("ADF type must be 'doc'")
        return v
```

### 7. jira.link_issues

#### Input Schema
```python
class JiraLinkIssuesParams(BaseModel):
    inward_issue: str = Field(..., regex=r"^[A-Z]+-\d+$", description="Source issue")
    outward_issue: str = Field(..., regex=r"^[A-Z]+-\d+$", description="Target issue")
    link_type: str = Field(..., description="Link type (e.g., 'blocks', 'relates to')")
    instance_id: Optional[UUID] = None
    idempotency_key: Optional[str] = Field(None, regex=r"^[a-zA-Z0-9-_]{1,64}$")
    comment: Optional[str] = Field(None, max_length=5000)
```

## 🗄️ SQL Query Templates (Detailed)

### 1. search_issues_by_project

#### Parameters
```python
class SearchIssuesByProjectParams(BaseModel):
    project_key: str = Field(..., regex=r"^[A-Z0-9-]+$", max_length=50)
    status: Optional[str] = Field(None, max_length=100)
    assignee: Optional[str] = Field(None, max_length=255)
    priority: Optional[str] = Field(None, max_length=50)
    limit: int = Field(50, ge=1, le=100)
    tenant_id: str = Field(..., description="Tenant ID from auth context")
```

#### SQL Template
```sql
-- Optimized with indexes: ix_work_items_tenant_project_status
SELECT 
    id,
    source,
    source_key,
    project_key,
    title,
    type,
    priority,
    status,
    assignee,
    reporter,
    created_at,
    updated_at,
    closed_at,
    labels
FROM work_items
WHERE tenant_id = :tenant_id
  AND project_key = :project_key
  AND (:status IS NULL OR status = :status)
  AND (:assignee IS NULL OR assignee = :assignee)
  AND (:priority IS NULL OR priority = :priority)
ORDER BY updated_at DESC
LIMIT :limit;
```

#### Expected Performance
- **Index used:** `ix_work_items_tenant_project_status`
- **Expected rows:** 10-1000
- **Target time:** < 50ms (p95)

### 2. get_project_metrics

#### Parameters
```python
class GetProjectMetricsParams(BaseModel):
    project_key: str = Field(..., regex=r"^[A-Z0-9-]+$", max_length=50)
    days: int = Field(30, ge=1, le=365, description="Number of days to look back")
    tenant_id: str = Field(...)
```

#### SQL Template
```sql
-- Uses materialized view: work_item_metrics_daily
SELECT 
    date,
    created,
    closed,
    wip,
    wip_no_assignee,
    stuck_gt_x_days,
    reopened,
    lead_time_p50_days,
    lead_time_p90_days,
    lead_time_avg_days,
    sla_at_risk,
    sla_breached,
    created_4w_avg,
    closed_4w_avg,
    created_delta_pct,
    closed_delta_pct
FROM work_item_metrics_daily
WHERE tenant_id = :tenant_id
  AND project_key = :project_key
  AND date >= CURRENT_DATE - INTERVAL ':days days'
ORDER BY date DESC;
```

#### Expected Performance
- **Index used:** `ix_wimd_tenant_project_date`
- **Expected rows:** 1-365
- **Target time:** < 20ms (p95)

### 3. search_issues_by_text

#### Parameters
```python
class SearchIssuesByTextParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    project_keys: List[str] = Field(..., min_items=1, max_items=50, description="Projects to search")
    limit: int = Field(20, ge=1, le=100)
    tenant_id: str = Field(...)
    
    @validator("project_keys")
    def validate_project_keys(cls, v):
        for key in v:
            if not re.match(r"^[A-Z0-9-]+$", key):
                raise ValueError(f"Invalid project key: {key}")
        return v
```

#### SQL Template
```sql
-- Uses trigram index: ix_work_items_title_trgm
SELECT 
    id,
    source,
    source_key,
    project_key,
    title,
    type,
    status,
    assignee,
    updated_at,
    similarity(title, :query) as sim_score
FROM work_items
WHERE tenant_id = :tenant_id
  AND project_key = ANY(:project_keys)
  AND title % :query  -- Trigram similarity operator
ORDER BY similarity(title, :query) DESC, updated_at DESC
LIMIT :limit;
```

#### Expected Performance
- **Index used:** `ix_work_items_title_trgm` (GIN)
- **Expected rows:** 0-100
- **Target time:** < 100ms (p95)

### 4. get_issue_history

#### Parameters
```python
class GetIssueHistoryParams(BaseModel):
    issue_key: str = Field(..., regex=r"^[A-Z]+-\d+$")
    tenant_id: str = Field(...)
    limit: int = Field(100, ge=1, le=500)
```

#### SQL Template
```sql
SELECT 
    t.id,
    t.from_status,
    t.to_status,
    t.timestamp,
    t.actor
FROM work_item_transitions t
JOIN work_items w ON t.work_item_id = w.id
WHERE w.tenant_id = :tenant_id
  AND w.source_key = :issue_key
ORDER BY t.timestamp DESC
LIMIT :limit;
```

### 5. get_user_workload

#### Parameters
```python
class GetUserWorkloadParams(BaseModel):
    assignee: str = Field(..., max_length=255)
    status: Optional[List[str]] = Field(None, max_items=20)
    tenant_id: str = Field(...)
```

#### SQL Template
```sql
SELECT 
    project_key,
    COUNT(*) as issue_count,
    COUNT(*) FILTER (WHERE priority = 'critical') as critical_count,
    COUNT(*) FILTER (WHERE priority = 'high') as high_count,
    COUNT(*) FILTER (WHERE is_stuck = true) as stuck_count,
    AVG(days_in_current_status) as avg_days_in_status
FROM work_items
WHERE tenant_id = :tenant_id
  AND assignee = :assignee
  AND (:status IS NULL OR status = ANY(:status))
GROUP BY project_key
ORDER BY issue_count DESC;
```

### 6. lead_time_metrics

#### Parameters
```python
class LeadTimeMetricsParams(BaseModel):
    project_key: Optional[str] = Field(None, regex=r"^[A-Z0-9-]+$")
    team: Optional[str] = Field(None, max_length=100)
    days: int = Field(30, ge=1, le=365)
    tenant_id: str = Field(...)
```

#### SQL Template
```sql
SELECT 
    date,
    project_key,
    team,
    lead_time_p50_days,
    lead_time_p90_days,
    lead_time_avg_days,
    closed as throughput
FROM work_item_metrics_daily
WHERE tenant_id = :tenant_id
  AND (:project_key IS NULL OR project_key = :project_key)
  AND (:team IS NULL OR team = :team)
  AND date >= CURRENT_DATE - INTERVAL ':days days'
ORDER BY date DESC;
```

## 🔒 RLS Policies (Detailed)

### Policy Predicates

#### tenants
```sql
-- SELECT policy
CREATE POLICY tenant_select ON tenants FOR SELECT
  USING (id = current_setting('app.current_tenant_id', true)::uuid);

-- No INSERT/UPDATE/DELETE for regular users (admin only)
```

#### jira_instances
```sql
-- SELECT policy
CREATE POLICY instance_select ON jira_instances FOR SELECT
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- INSERT policy
CREATE POLICY instance_insert ON jira_instances FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- UPDATE policy
CREATE POLICY instance_update ON jira_instances FOR UPDATE
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- DELETE policy
CREATE POLICY instance_delete ON jira_instances FOR DELETE
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
```

#### work_items
```sql
-- SELECT policy
CREATE POLICY work_item_select ON work_items FOR SELECT
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- INSERT policy (for sync operations)
CREATE POLICY work_item_insert ON work_items FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- UPDATE policy (for sync operations)
CREATE POLICY work_item_update ON work_items FOR UPDATE
  USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- No DELETE (soft delete only via is_deleted flag)
```

### Session Context Setup

```python
from contextvars import ContextVar

# Context variable for current tenant
current_tenant_id: ContextVar[Optional[UUID]] = ContextVar("current_tenant_id", default=None)

@event.listens_for(Engine, "connect")
def set_tenant_context(dbapi_conn, connection_record):
    """Set tenant context for RLS on new connections."""
    pass  # Will be set per-request

@event.listens_for(Engine, "begin")
def receive_begin(conn):
    """Set tenant context at transaction begin."""
    tenant_id = current_tenant_id.get()
    if tenant_id:
        conn.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
```

## 🚨 Error Model (Complete)

```python
class MCPErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    UPSTREAM_4XX = "upstream_4xx"
    UPSTREAM_5XX = "upstream_5xx"
    CONFLICT = "conflict"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"

class MCPError(BaseModel):
    code: MCPErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None  # Seconds (for rate_limited)
    request_id: str  # For tracing
    timestamp: datetime
```

### Error Handling Examples

```python
# Validation error
{
  "code": "validation_error",
  "message": "Invalid JQL query",
  "details": {
    "field": "query",
    "error": "Forbidden keyword: DROP"
  },
  "request_id": "req_123",
  "timestamp": "2025-10-03T10:30:00Z"
}

# Rate limited
{
  "code": "rate_limited",
  "message": "Rate limit exceeded for instance",
  "details": {
    "instance_id": "uuid",
    "limit": 100,
    "window": "1m"
  },
  "retry_after": 60,
  "request_id": "req_124",
  "timestamp": "2025-10-03T10:31:00Z"
}
```

---

**Version:** 1.0.0  
**Created:** 2025-10-03  
**Status:** Draft

