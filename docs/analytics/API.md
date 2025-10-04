# Analytics API Reference

## Base URL

```
/analytics
```

## Authentication

All endpoints require authentication via the `Authorization` header and tenant identification via the `X-Tenant-ID` header.

```http
Authorization: Bearer <token>
X-Tenant-ID: <tenant-uuid>
```

---

## Endpoints

### 1. Execute Analytics Query

Execute an analytics query from AnalyticsSpec.

**Endpoint:** `POST /analytics/query`

**Request Body:**
```json
{
  "entity": "issues",
  "metrics": [
    {
      "name": "total_issues",
      "aggregation": "count"
    }
  ],
  "filters": [
    {
      "field": "status",
      "operator": "eq",
      "value": "Done"
    }
  ],
  "group_by": [
    {
      "field": "assignee_name"
    }
  ],
  "sort_by": [
    {
      "field": "total_issues",
      "direction": "desc"
    }
  ],
  "limit": 10
}
```

**Query Parameters:**
- `use_cache` (boolean, default: true) - Use cache if available
- `cache_ttl_hours` (integer, 1-168, default: 24) - Cache TTL in hours

**Response (200 OK):**
```json
{
  "data": [
    {
      "assignee_name": "John Doe",
      "total_issues": 42
    },
    {
      "assignee_name": "Jane Smith",
      "total_issues": 38
    }
  ],
  "metadata": {
    "row_count": 2,
    "execution_time_ms": 150,
    "sql_query": "SELECT ...",
    "spec": {...},
    "executed_at": "2024-01-15T10:30:00Z",
    "cached": false
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": {
    "message": "Invalid AnalyticsSpec",
    "errors": [
      "Invalid field 'invalid_field' for entity 'issues'"
    ],
    "warnings": []
  }
}
```

---

### 2. Execute Natural Language Query

Execute an analytics query from natural language.

**Endpoint:** `POST /analytics/query/nl`

**Request Body:**
```json
{
  "query": "Show me the top 10 assignees by number of completed issues"
}
```

**Query Parameters:**
- `use_cache` (boolean, default: true)
- `cache_ttl_hours` (integer, 1-168, default: 24)

**Response (200 OK):**
```json
{
  "data": [...],
  "metadata": {...},
  "translated_spec": {
    "entity": "issues",
    "metrics": [...],
    "filters": [...],
    "group_by": [...],
    "sort_by": [...],
    "limit": 10
  },
  "original_query": "Show me the top 10 assignees by number of completed issues"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": {
    "message": "Failed to translate query",
    "error": "Could not parse query"
  }
}
```

---

### 3. Validate Analytics Spec

Validate an AnalyticsSpec without executing it.

**Endpoint:** `POST /analytics/query/validate`

**Request Body:**
```json
{
  "entity": "issues",
  "metrics": [
    {
      "name": "total",
      "aggregation": "count"
    }
  ]
}
```

**Query Parameters:**
- `is_job` (boolean, default: false) - Whether this is a background job

**Response (200 OK):**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [
    "Large limit (500) may impact performance"
  ]
}
```

---

### 4. Get Available Metrics

List available metrics for the tenant.

**Endpoint:** `GET /analytics/metrics`

**Query Parameters:**
- `category` (string, optional) - Filter by category
- `tags` (string, optional) - Filter by tags (comma-separated)

**Response (200 OK):**
```json
{
  "metrics": [
    {
      "name": "sprint_velocity",
      "display_name": "Sprint Velocity",
      "description": "Average story points completed per sprint",
      "category": "velocity",
      "parameters": ["tenant_id", "instance_id", "start_date", "end_date"],
      "required_parameters": ["tenant_id", "instance_id", "start_date", "end_date"],
      "unit": "points",
      "tags": ["agile", "scrum", "velocity", "sprint"]
    }
  ],
  "count": 10
}
```

---

### 5. Search Metrics

Search metrics by name or description.

**Endpoint:** `GET /analytics/metrics/search`

**Query Parameters:**
- `q` (string, required) - Search query
- `limit` (integer, 1-50, default: 10) - Maximum results

**Response (200 OK):**
```json
{
  "metrics": [
    {
      "name": "sprint_velocity",
      "display_name": "Sprint Velocity",
      "description": "Average story points completed per sprint",
      "category": "velocity",
      "unit": "points"
    }
  ],
  "count": 1,
  "query": "velocity"
}
```

---

### 6. Invalidate Cache

Invalidate analytics cache.

**Endpoint:** `POST /analytics/cache/invalidate`

**Request Body (Optional):**
```json
{
  "entity": "issues",
  "metrics": [...]
}
```

If no body is provided, invalidates all cache for the tenant.

**Response (200 OK):**
```json
{
  "invalidated_count": 5,
  "scope": "specific"
}
```

---

### 7. Get Cache Statistics

Get cache statistics for the tenant.

**Endpoint:** `GET /analytics/cache/stats`

**Response (200 OK):**
```json
{
  "total_entries": 100,
  "active_entries": 85,
  "expired_entries": 15,
  "total_cached_rows": 10000,
  "avg_execution_time_ms": 250,
  "avg_age_seconds": 3600
}
```

---

### 8. Clean Up Expired Cache

Clean up expired cache entries.

**Endpoint:** `POST /analytics/cache/cleanup`

**Response (200 OK):**
```json
{
  "removed_count": 15
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

---

## Rate Limits

- **Interactive queries**: Max 1000 results
- **Background jobs**: Max 100,000 results
- **API calls**: 100 requests per minute per tenant

---

## Examples

### Example 1: Count Issues by Status

```bash
curl -X POST "https://api.example.com/analytics/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: <tenant-uuid>" \
  -H "Content-Type: application/json" \
  -d '{
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
    ]
  }'
```

### Example 2: Average Cycle Time

```bash
curl -X POST "https://api.example.com/analytics/query" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: <tenant-uuid>" \
  -H "Content-Type: application/json" \
  -d '{
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
    ]
  }'
```

### Example 3: Natural Language Query

```bash
curl -X POST "https://api.example.com/analytics/query/nl" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: <tenant-uuid>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me sprint velocity over the last 6 months"
  }'
```

### Example 4: Search Metrics

```bash
curl -X GET "https://api.example.com/analytics/metrics/search?q=velocity&limit=5" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: <tenant-uuid>"
```

---

## Best Practices

1. **Use caching** - Enable caching for frequently executed queries
2. **Add filters** - Reduce result set size with appropriate filters
3. **Limit results** - Use `limit` to prevent large result sets
4. **Validate first** - Use `/analytics/query/validate` before executing expensive queries
5. **Monitor cache** - Check cache stats regularly and clean up expired entries
6. **Use predefined metrics** - Leverage predefined metrics when possible
7. **Batch queries** - Combine multiple metrics in a single query when possible

