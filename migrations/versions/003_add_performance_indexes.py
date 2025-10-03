"""Add performance indexes

Revision ID: 003_performance_indexes
Revises: 7f39d8475ecd
Create Date: 2025-10-03 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_performance_indexes'
down_revision = '7f39d8475ecd'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes."""

    # ============================================================================
    # Issues Table Indexes
    # ============================================================================

    # Full-text search index on summary and description (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_summary_trgm
        ON issues USING gin (summary gin_trgm_ops)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_description_trgm
        ON issues USING gin (description gin_trgm_ops)
    """)

    # Composite index for common queries (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_instance_project_status
        ON issues (instance_id, project_id, status)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_instance_assignee_status
        ON issues (instance_id, assignee_account_id, status)
    """)

    # Index for time-based queries (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_jira_created_at
        ON issues (jira_created_at)
    """)

    # Index for resolved issues (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_resolved_at
        ON issues (resolved_at) WHERE resolved_at IS NOT NULL
    """)

    # Index for labels (GIN for array) (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_labels_gin
        ON issues USING gin (labels)
    """)

    # Index for components (GIN for array) (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_issues_components_gin
        ON issues USING gin (components)
    """)
    
    # ============================================================================
    # Projects Table Indexes
    # ============================================================================

    # Full-text search on project name (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_projects_name_trgm
        ON projects USING gin (name gin_trgm_ops)
    """)

    # Index for active projects (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_projects_instance_active
        ON projects (instance_id, is_archived)
    """)

    # ============================================================================
    # Users Table Indexes
    # ============================================================================

    # Full-text search on display name (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_display_name_trgm
        ON users USING gin (display_name gin_trgm_ops)
    """)

    # Index for active users (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_instance_active
        ON users (instance_id, is_active)
    """)

    # Index for account type (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_users_account_type
        ON users (account_type)
    """)
    
    # ============================================================================
    # Comments Table Indexes
    # ============================================================================

    # Full-text search on comment body (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_comments_body_trgm
        ON comments USING gin (body gin_trgm_ops)
    """)

    # Index for public comments (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_comments_issue_public
        ON comments (issue_id, is_public)
    """)

    # Index for author (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_comments_author
        ON comments (author_account_id)
    """)

    # ============================================================================
    # Changelogs Table Indexes
    # ============================================================================

    # Index for author (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_changelogs_author
        ON changelogs (author_account_id)
    """)

    # Index for time-based queries (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_changelogs_instance_created
        ON changelogs (instance_id, jira_created_at)
    """)
    
    # ============================================================================
    # Jira Instances Table Indexes
    # ============================================================================

    # Index for active instances (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_jira_instances_tenant_active
        ON jira_instances (tenant_id, is_active)
    """)

    # Index for connected instances (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_jira_instances_is_connected
        ON jira_instances (is_connected)
    """)

    # Index for sync-enabled instances (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_jira_instances_sync_enabled
        ON jira_instances (sync_enabled)
    """)

    # Index for last sync time (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_jira_instances_last_sync
        ON jira_instances (last_sync_at)
    """)

    # ============================================================================
    # Tenants Table Indexes
    # ============================================================================

    # Index for active tenants (NEW)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenants_is_active
        ON tenants (is_active)
    """)


def downgrade():
    """Remove performance indexes."""
    
    # Issues
    op.drop_index('ix_issues_summary_trgm', table_name='issues')
    op.drop_index('ix_issues_description_trgm', table_name='issues')
    op.drop_index('ix_issues_instance_project_status', table_name='issues')
    op.drop_index('ix_issues_instance_assignee_status', table_name='issues')
    op.drop_index('ix_issues_jira_created_at', table_name='issues')
    op.drop_index('ix_issues_resolved_at', table_name='issues')
    op.drop_index('ix_issues_parent_id', table_name='issues')
    op.drop_index('ix_issues_labels_gin', table_name='issues')
    op.drop_index('ix_issues_components_gin', table_name='issues')
    
    # Projects
    op.drop_index('ix_projects_name_trgm', table_name='projects')
    op.drop_index('ix_projects_instance_active', table_name='projects')
    
    # Users
    op.drop_index('ix_users_display_name_trgm', table_name='users')
    op.drop_index('ix_users_instance_active', table_name='users')
    op.drop_index('ix_users_account_type', table_name='users')
    
    # Comments
    op.drop_index('ix_comments_body_trgm', table_name='comments')
    op.drop_index('ix_comments_issue_public', table_name='comments')
    op.drop_index('ix_comments_author', table_name='comments')
    
    # Changelogs
    op.drop_index('ix_changelogs_author', table_name='changelogs')
    op.drop_index('ix_changelogs_instance_created', table_name='changelogs')
    
    # Jira Instances
    op.drop_index('ix_jira_instances_tenant_active', table_name='jira_instances')
    op.drop_index('ix_jira_instances_is_connected', table_name='jira_instances')
    op.drop_index('ix_jira_instances_sync_enabled', table_name='jira_instances')
    op.drop_index('ix_jira_instances_last_sync', table_name='jira_instances')
    
    # Tenants
    op.drop_index('ix_tenants_is_active', table_name='tenants')

