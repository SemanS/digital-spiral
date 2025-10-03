"""Add row-level security policies

Revision ID: 004_row_level_security
Revises: 003_performance_indexes
Create Date: 2025-10-03 15:30:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '004_row_level_security'
down_revision = '003_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Enable row-level security and create policies."""
    
    # ============================================================================
    # Enable RLS on all tenant-scoped tables
    # ============================================================================
    
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE jira_instances ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE issues ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE projects ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE comments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE changelogs ENABLE ROW LEVEL SECURITY")
    
    # ============================================================================
    # Create RLS policies for tenants table
    # ============================================================================
    
    # Policy: Users can only see their own tenant
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON tenants
        FOR ALL
        USING (id = current_setting('app.current_tenant_id', TRUE)::uuid)
    """)
    
    # ============================================================================
    # Create RLS policies for jira_instances table
    # ============================================================================
    
    # Policy: Users can only see instances for their tenant
    op.execute("""
        CREATE POLICY jira_instances_tenant_isolation_policy ON jira_instances
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    """)
    
    # ============================================================================
    # Create RLS policies for issues table
    # ============================================================================
    
    # Policy: Users can only see issues for their tenant
    op.execute("""
        CREATE POLICY issues_tenant_isolation_policy ON issues
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    """)
    
    # ============================================================================
    # Create RLS policies for projects table
    # ============================================================================
    
    # Policy: Users can only see projects for their tenant
    op.execute("""
        CREATE POLICY projects_tenant_isolation_policy ON projects
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    """)
    
    # ============================================================================
    # Create RLS policies for users table
    # ============================================================================
    
    # Policy: Users can only see users for their tenant
    op.execute("""
        CREATE POLICY users_tenant_isolation_policy ON users
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    """)
    
    # ============================================================================
    # Create RLS policies for comments table
    # ============================================================================
    
    # Policy: Users can only see comments for their tenant
    op.execute("""
        CREATE POLICY comments_tenant_isolation_policy ON comments
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    """)
    
    # ============================================================================
    # Create RLS policies for changelogs table
    # ============================================================================
    
    # Policy: Users can only see changelogs for their tenant
    op.execute("""
        CREATE POLICY changelogs_tenant_isolation_policy ON changelogs
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::uuid)
    """)
    
    # ============================================================================
    # Create helper function to set tenant context
    # ============================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION set_tenant_context(tenant_uuid uuid)
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant_id', tenant_uuid::text, FALSE);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
    
    # ============================================================================
    # Create helper function to get current tenant
    # ============================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION get_current_tenant()
        RETURNS uuid AS $$
        BEGIN
            RETURN current_setting('app.current_tenant_id', TRUE)::uuid;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)
    
    # ============================================================================
    # Create helper function to clear tenant context
    # ============================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION clear_tenant_context()
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant_id', '', FALSE);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)


def downgrade():
    """Disable row-level security and drop policies."""
    
    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS set_tenant_context(uuid)")
    op.execute("DROP FUNCTION IF EXISTS get_current_tenant()")
    op.execute("DROP FUNCTION IF EXISTS clear_tenant_context()")
    
    # Drop policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON tenants")
    op.execute("DROP POLICY IF EXISTS jira_instances_tenant_isolation_policy ON jira_instances")
    op.execute("DROP POLICY IF EXISTS issues_tenant_isolation_policy ON issues")
    op.execute("DROP POLICY IF EXISTS projects_tenant_isolation_policy ON projects")
    op.execute("DROP POLICY IF EXISTS users_tenant_isolation_policy ON users")
    op.execute("DROP POLICY IF EXISTS comments_tenant_isolation_policy ON comments")
    op.execute("DROP POLICY IF EXISTS changelogs_tenant_isolation_policy ON changelogs")
    
    # Disable RLS
    op.execute("ALTER TABLE changelogs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE comments DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE projects DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE issues DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE jira_instances DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tenants DISABLE ROW LEVEL SECURITY")

