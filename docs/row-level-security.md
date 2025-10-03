# Row-Level Security (RLS)

This document describes the Row-Level Security implementation in Digital Spiral for multi-tenant data isolation.

## Overview

Row-Level Security (RLS) is a PostgreSQL feature that allows you to control which rows users can access in a table. In Digital Spiral, we use RLS to ensure complete data isolation between tenants.

## How It Works

### 1. Session Variable

Each database session sets a `app.current_tenant_id` configuration variable:

```sql
SET app.current_tenant_id = '550e8400-e29b-41d4-a716-446655440000';
```

### 2. RLS Policies

Each tenant-scoped table has an RLS policy that filters rows based on the current tenant:

```sql
CREATE POLICY tenant_isolation_policy ON issues
FOR ALL
USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid);
```

### 3. Automatic Filtering

Once RLS is enabled and the tenant context is set, all queries are automatically filtered:

```sql
-- This query only returns issues for the current tenant
SELECT * FROM issues;

-- Even with explicit WHERE clause, other tenants' data is inaccessible
SELECT * FROM issues WHERE tenant_id = 'other-tenant-id';  -- Returns nothing
```

## Tables with RLS

The following tables have RLS enabled:

1. `tenants` - Tenant master data
2. `jira_instances` - Jira instance configurations
3. `issues` - Jira issues
4. `projects` - Jira projects
5. `users` - Jira users
6. `comments` - Issue comments
7. `changelogs` - Issue change history

## Helper Functions

### set_tenant_context(tenant_uuid)

Sets the current tenant context for the session.

```sql
SELECT set_tenant_context('550e8400-e29b-41d4-a716-446655440000');
```

**Usage in Python:**

```python
from sqlalchemy import text

# Set tenant context
session.execute(
    text("SELECT set_tenant_context(:tenant_id)"),
    {"tenant_id": str(tenant_id)}
)

# Now all queries are scoped to this tenant
issues = session.query(Issue).all()
```

### get_current_tenant()

Returns the current tenant ID.

```sql
SELECT get_current_tenant();
```

**Usage in Python:**

```python
from sqlalchemy import text

result = session.execute(text("SELECT get_current_tenant()"))
current_tenant_id = result.scalar()
```

### clear_tenant_context()

Clears the tenant context (useful for admin operations).

```sql
SELECT clear_tenant_context();
```

**Usage in Python:**

```python
from sqlalchemy import text

session.execute(text("SELECT clear_tenant_context()"))
```

## Application Integration

### Setting Tenant Context

The tenant context should be set at the beginning of each request:

```python
from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session

@contextmanager
def tenant_context(session: Session, tenant_id: uuid.UUID):
    """Context manager for setting tenant context."""
    try:
        # Set tenant context
        session.execute(
            text("SELECT set_tenant_context(:tenant_id)"),
            {"tenant_id": str(tenant_id)}
        )
        yield session
    finally:
        # Clear tenant context
        session.execute(text("SELECT clear_tenant_context()"))
```

**Usage:**

```python
with tenant_context(session, tenant_id):
    # All queries within this block are scoped to the tenant
    issues = session.query(Issue).all()
    projects = session.query(Project).all()
```

### FastAPI Middleware

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant ID from request (e.g., from JWT, subdomain, header)
        tenant_id = extract_tenant_id(request)
        
        # Set tenant context in database session
        db = request.state.db
        db.execute(
            text("SELECT set_tenant_context(:tenant_id)"),
            {"tenant_id": str(tenant_id)}
        )
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Clear tenant context
            db.execute(text("SELECT clear_tenant_context()"))
```

## Security Considerations

### 1. Always Set Tenant Context

**IMPORTANT:** Always set the tenant context before executing queries. Without it, RLS policies will deny access to all rows.

```python
# ❌ BAD - No tenant context
issues = session.query(Issue).all()  # Returns empty list

# ✅ GOOD - With tenant context
with tenant_context(session, tenant_id):
    issues = session.query(Issue).all()  # Returns tenant's issues
```

### 2. Bypass RLS for Admin Operations

For admin operations that need to access all tenants' data, you can temporarily disable RLS:

```sql
-- Disable RLS for current session (requires superuser or table owner)
SET row_security = OFF;

-- Your admin queries here
SELECT * FROM issues;

-- Re-enable RLS
SET row_security = ON;
```

**In Python:**

```python
from sqlalchemy import text

# Disable RLS (use with caution!)
session.execute(text("SET row_security = OFF"))

try:
    # Admin queries
    all_issues = session.query(Issue).all()
finally:
    # Re-enable RLS
    session.execute(text("SET row_security = ON"))
```

### 3. Connection Pooling

When using connection pooling, ensure the tenant context is cleared when returning connections to the pool:

```python
from sqlalchemy.pool import Pool
from sqlalchemy import event

@event.listens_for(Pool, "checkin")
def clear_tenant_on_checkin(dbapi_conn, connection_record):
    """Clear tenant context when connection is returned to pool."""
    cursor = dbapi_conn.cursor()
    cursor.execute("SELECT clear_tenant_context()")
    cursor.close()
```

## Testing RLS

### Test Tenant Isolation

```python
import pytest
from sqlalchemy import text

def test_tenant_isolation(session, tenant1_id, tenant2_id):
    """Test that tenants cannot access each other's data."""
    
    # Create issue for tenant 1
    with tenant_context(session, tenant1_id):
        issue1 = Issue(
            tenant_id=tenant1_id,
            issue_key="T1-1",
            summary="Tenant 1 issue"
        )
        session.add(issue1)
        session.commit()
    
    # Create issue for tenant 2
    with tenant_context(session, tenant2_id):
        issue2 = Issue(
            tenant_id=tenant2_id,
            issue_key="T2-1",
            summary="Tenant 2 issue"
        )
        session.add(issue2)
        session.commit()
    
    # Verify tenant 1 can only see their issue
    with tenant_context(session, tenant1_id):
        issues = session.query(Issue).all()
        assert len(issues) == 1
        assert issues[0].issue_key == "T1-1"
    
    # Verify tenant 2 can only see their issue
    with tenant_context(session, tenant2_id):
        issues = session.query(Issue).all()
        assert len(issues) == 1
        assert issues[0].issue_key == "T2-1"
```

### Test RLS Enforcement

```python
def test_rls_enforcement(session, tenant1_id, tenant2_id):
    """Test that RLS prevents cross-tenant access."""
    
    # Create issue for tenant 1
    with tenant_context(session, tenant1_id):
        issue = Issue(
            tenant_id=tenant1_id,
            issue_key="T1-1",
            summary="Tenant 1 issue"
        )
        session.add(issue)
        session.commit()
        issue_id = issue.id
    
    # Try to access tenant 1's issue from tenant 2's context
    with tenant_context(session, tenant2_id):
        # Even with explicit ID, should not be accessible
        issue = session.query(Issue).filter_by(id=issue_id).first()
        assert issue is None
```

## Monitoring RLS

### Check RLS Status

```sql
SELECT 
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### View RLS Policies

```sql
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
```

### Check Current Tenant Context

```sql
SELECT current_setting('app.current_tenant_id', TRUE) AS current_tenant;
```

## Performance Impact

RLS policies add a WHERE clause to every query, which can impact performance. To minimize impact:

1. **Ensure tenant_id is indexed** on all tables (already done)
2. **Use composite indexes** that include tenant_id for common queries
3. **Monitor query performance** with EXPLAIN ANALYZE
4. **Consider partitioning** for very large tables (future optimization)

### Example Query Plan

```sql
EXPLAIN ANALYZE
SELECT * FROM issues WHERE status = 'Open';

-- With RLS enabled, the plan includes:
-- Filter: (tenant_id = current_setting('app.current_tenant_id'::text, true)::uuid)
```

## Troubleshooting

### Issue: Queries return no results

**Cause:** Tenant context not set

**Solution:**
```python
# Check current tenant
result = session.execute(text("SELECT get_current_tenant()"))
print(result.scalar())  # Should not be None

# Set tenant context
session.execute(
    text("SELECT set_tenant_context(:tenant_id)"),
    {"tenant_id": str(tenant_id)}
)
```

### Issue: Permission denied errors

**Cause:** RLS policy denying access

**Solution:** Ensure the user has appropriate permissions and the tenant context is correctly set.

### Issue: Admin queries failing

**Cause:** RLS blocking admin access

**Solution:** Temporarily disable RLS for admin operations:
```python
session.execute(text("SET row_security = OFF"))
```

## Best Practices

1. ✅ **Always use tenant context managers** to ensure cleanup
2. ✅ **Set tenant context in middleware** for web applications
3. ✅ **Clear tenant context** when returning connections to pool
4. ✅ **Test tenant isolation** thoroughly
5. ✅ **Monitor RLS performance** impact
6. ✅ **Document admin bypass procedures** for emergency access
7. ❌ **Never hardcode tenant IDs** in queries
8. ❌ **Never disable RLS globally** in production

