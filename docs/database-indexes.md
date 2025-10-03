# Database Indexes

This document describes the database indexes used in Digital Spiral for performance optimization.

## Overview

The database uses a combination of B-tree, GIN (Generalized Inverted Index), and trigram indexes to optimize different types of queries.

## Index Types

### 1. B-tree Indexes (Default)
Used for equality and range queries on single or multiple columns.

### 2. GIN Indexes
Used for:
- JSONB columns (for querying nested data)
- Array columns (for containment queries)
- Full-text search with trigram operators

### 3. Trigram Indexes (pg_trgm)
Used for fuzzy text search and LIKE/ILIKE queries.

## Issues Table Indexes

### Primary & Foreign Keys
- `issues_pkey` - Primary key on `id`
- `ix_issues_instance_id` - Foreign key to jira_instances
- `ix_issues_project_id` - Foreign key to projects
- `ix_issues_parent_id` - Foreign key to parent issue (for subtasks)
- `ix_issues_tenant_id` - Foreign key to tenants

### Search Indexes
- `ix_issues_issue_key` - Unique index on issue key (e.g., "PROJ-123")
- `ix_issues_issue_id` - Index on Jira internal ID
- `ix_issues_summary_trgm` - **GIN trigram** for fuzzy search on summary
- `ix_issues_description_trgm` - **GIN trigram** for fuzzy search on description

### Status & Type Indexes
- `ix_issues_status` - Index on issue status
- `ix_issues_issue_type` - Index on issue type
- `ix_issues_priority` - Index on priority

### Assignment Indexes
- `ix_issues_assignee_account_id` - Index on assignee
- `ix_issues_reporter_account_id` - Index on reporter

### Composite Indexes (for common queries)
- `ix_issues_instance_project` - (instance_id, project_id)
- `ix_issues_instance_status` - (instance_id, status)
- `ix_issues_instance_assignee` - (instance_id, assignee_account_id)
- `ix_issues_instance_updated` - (instance_id, jira_updated_at)
- `ix_issues_tenant_instance` - (tenant_id, instance_id)
- `ix_issues_instance_project_status` - (instance_id, project_id, status)
- `ix_issues_instance_assignee_status` - (instance_id, assignee_account_id, status)

### Time-based Indexes
- `ix_issues_jira_updated_at` - Index on last update time
- `ix_issues_jira_created_at` - Index on creation time
- `ix_issues_resolved_at` - Partial index on resolved time (WHERE resolved_at IS NOT NULL)

### JSONB Indexes
- `ix_issues_custom_fields` - **GIN** index on custom_fields JSONB
- `ix_issues_raw_jsonb` - **GIN** index on raw_jsonb

### Array Indexes
- `ix_issues_labels_gin` - **GIN** index on labels array
- `ix_issues_components_gin` - **GIN** index on components array

## Projects Table Indexes

### Primary & Foreign Keys
- `projects_pkey` - Primary key on `id`
- `ix_projects_instance_id` - Foreign key to jira_instances
- `ix_projects_tenant_id` - Foreign key to tenants

### Search Indexes
- `ix_projects_project_key` - Index on project key
- `ix_projects_project_id` - Index on Jira internal ID
- `ix_projects_name_trgm` - **GIN trigram** for fuzzy search on name

### Composite Indexes
- `ix_projects_instance_key` - **UNIQUE** (instance_id, project_key)
- `ix_projects_tenant_instance` - (tenant_id, instance_id)
- `ix_projects_instance_active` - (instance_id, is_archived)

### Status Indexes
- `ix_projects_is_archived` - Index on archived status

### JSONB Indexes
- `ix_projects_raw_jsonb` - **GIN** index on raw_jsonb

## Users Table Indexes

### Primary & Foreign Keys
- `users_pkey` - Primary key on `id`
- `ix_users_instance_id` - Foreign key to jira_instances
- `ix_users_tenant_id` - Foreign key to tenants

### Search Indexes
- `ix_users_account_id` - Index on Jira account ID
- `ix_users_email_address` - Index on email
- `ix_users_display_name_trgm` - **GIN trigram** for fuzzy search on display name

### Composite Indexes
- `ix_users_instance_account` - **UNIQUE** (instance_id, account_id)
- `ix_users_tenant_instance` - (tenant_id, instance_id)
- `ix_users_instance_active` - (instance_id, is_active)

### Status Indexes
- `ix_users_is_active` - Index on active status
- `ix_users_account_type` - Index on account type

### JSONB Indexes
- `ix_users_raw_jsonb` - **GIN** index on raw_jsonb

## Comments Table Indexes

### Primary & Foreign Keys
- `comments_pkey` - Primary key on `id`
- `ix_comments_instance_id` - Foreign key to jira_instances
- `ix_comments_issue_id` - Foreign key to issues
- `ix_comments_tenant_id` - Foreign key to tenants

### Search Indexes
- `ix_comments_comment_id` - Index on Jira internal ID
- `ix_comments_issue_key` - Index on issue key
- `ix_comments_body_trgm` - **GIN trigram** for fuzzy search on body

### Composite Indexes
- `ix_comments_instance_comment` - **UNIQUE** (instance_id, comment_id)
- `ix_comments_issue_created` - (issue_id, jira_created_at)
- `ix_comments_tenant_instance` - (tenant_id, instance_id)
- `ix_comments_issue_public` - (issue_id, is_public)

### Author Indexes
- `ix_comments_author_account_id` - Index on author
- `ix_comments_author` - Index on author (duplicate, can be removed)

### JSONB Indexes
- `ix_comments_raw_jsonb` - **GIN** index on raw_jsonb

## Changelogs Table Indexes

### Primary & Foreign Keys
- `changelogs_pkey` - Primary key on `id`
- `ix_changelogs_instance_id` - Foreign key to jira_instances
- `ix_changelogs_issue_id` - Foreign key to issues
- `ix_changelogs_tenant_id` - Foreign key to tenants

### Search Indexes
- `ix_changelogs_changelog_id` - Index on Jira internal ID
- `ix_changelogs_issue_key` - Index on issue key

### Composite Indexes
- `ix_changelogs_instance_changelog` - **UNIQUE** (instance_id, changelog_id)
- `ix_changelogs_issue_created` - (issue_id, jira_created_at)
- `ix_changelogs_tenant_instance` - (tenant_id, instance_id)
- `ix_changelogs_instance_created` - (instance_id, jira_created_at)

### Author Indexes
- `ix_changelogs_author_account_id` - Index on author
- `ix_changelogs_author` - Index on author (duplicate, can be removed)

### Time-based Indexes
- `ix_changelogs_jira_created_at` - Index on creation time

### JSONB Indexes
- `ix_changelogs_items` - **GIN** index on items JSONB array
- `ix_changelogs_raw_jsonb` - **GIN** index on raw_jsonb

## Jira Instances Table Indexes

### Primary & Foreign Keys
- `jira_instances_pkey` - Primary key on `id`
- `ix_jira_instances_tenant_id` - Foreign key to tenants

### Composite Indexes
- `ix_jira_instances_tenant_active` - (tenant_id, is_active)

### Status Indexes
- `ix_jira_instances_is_active` - Index on active status
- `ix_jira_instances_is_connected` - Index on connection status
- `ix_jira_instances_sync_enabled` - Index on sync enabled status

### Time-based Indexes
- `ix_jira_instances_last_sync` - Index on last sync time

## Tenants Table Indexes

### Primary Key
- `tenants_pkey` - Primary key on `id`

### Unique Indexes
- `ix_tenants_slug` - **UNIQUE** index on slug

### Status Indexes
- `ix_tenants_is_active` - Index on active status

## Query Optimization Examples

### 1. Search issues by text
```sql
-- Uses ix_issues_summary_trgm
SELECT * FROM issues 
WHERE summary ILIKE '%bug%';
```

### 2. Get issues by project and status
```sql
-- Uses ix_issues_instance_project_status
SELECT * FROM issues 
WHERE instance_id = '...' 
  AND project_id = '...' 
  AND status = 'In Progress';
```

### 3. Get issues assigned to user
```sql
-- Uses ix_issues_instance_assignee_status
SELECT * FROM issues 
WHERE instance_id = '...' 
  AND assignee_account_id = '...' 
  AND status != 'Done';
```

### 4. Search issues by custom field
```sql
-- Uses ix_issues_custom_fields (GIN)
SELECT * FROM issues 
WHERE custom_fields @> '{"sprint": "Sprint 1"}';
```

### 5. Get issues with specific label
```sql
-- Uses ix_issues_labels_gin
SELECT * FROM issues 
WHERE labels @> ARRAY['bug'];
```

## Index Maintenance

### Analyze index usage
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Find unused indexes
```sql
SELECT 
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
  AND indexname NOT LIKE '%_pkey';
```

### Check index size
```sql
SELECT 
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Performance Considerations

1. **Trigram indexes** are larger than regular B-tree indexes but enable fast fuzzy search
2. **GIN indexes** on JSONB columns enable efficient querying of nested data
3. **Composite indexes** should match the most common query patterns
4. **Partial indexes** (with WHERE clause) are smaller and faster for filtered queries
5. Regular **VACUUM ANALYZE** is important for maintaining index performance

