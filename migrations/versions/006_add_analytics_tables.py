"""Add analytics tables for LLM + SQL Analytics System

Revision ID: 006_add_analytics_tables
Revises: 005_add_source_instances
Create Date: 2025-10-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_analytics_tables'
down_revision = '005_add_source_instances'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create sprints table
    op.create_table(
        'sprints',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sprint_id', sa.String(50), nullable=False),
        sa.Column('board_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),  # future, active, closed
        sa.Column('goal', sa.Text, nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('complete_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instance_id'], ['source_instances.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('instance_id', 'sprint_id', name='uq_sprints_instance_sprint'),
    )
    
    # Indexes for sprints
    op.create_index('idx_sprints_tenant_instance', 'sprints', ['tenant_id', 'instance_id'])
    op.create_index('idx_sprints_state', 'sprints', ['state'])
    op.create_index('idx_sprints_dates', 'sprints', ['start_date', 'end_date'])
    
    # 2. Create sprint_issues table
    op.create_table(
        'sprint_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sprint_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('removed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('story_points', sa.Float, nullable=True),
        sa.Column('completed', sa.Boolean, default=False, nullable=False),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('sprint_id', 'issue_id', name='uq_sprint_issues_sprint_issue'),
    )
    
    # Indexes for sprint_issues
    op.create_index('idx_sprint_issues_sprint', 'sprint_issues', ['sprint_id'])
    op.create_index('idx_sprint_issues_issue', 'sprint_issues', ['issue_id'])
    
    # 3. Create metrics_catalog table
    op.create_table(
        'metrics_catalog',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),  # velocity, quality, cycle_time, etc.
        sa.Column('sql_template', sa.Text, nullable=False),
        sa.Column('parameters', postgresql.JSONB, nullable=True),
        sa.Column('aggregation', sa.String(20), nullable=False),  # sum, avg, count, etc.
        sa.Column('unit', sa.String(20), nullable=True),  # points, days, count, etc.
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('embedding', postgresql.ARRAY(sa.Float), nullable=True),  # For semantic search
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_metrics_catalog_tenant_name'),
    )
    
    # Indexes for metrics_catalog
    op.create_index('idx_metrics_catalog_tenant', 'metrics_catalog', ['tenant_id'])
    op.create_index('idx_metrics_catalog_category', 'metrics_catalog', ['category'])
    op.create_index('idx_metrics_catalog_active', 'metrics_catalog', ['is_active'])
    
    # 4. Create analytics_jobs table
    op.create_table(
        'analytics_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),  # nl_query, spec_query, metric_query
        sa.Column('status', sa.String(20), nullable=False),  # pending, running, completed, failed
        sa.Column('input_data', postgresql.JSONB, nullable=False),
        sa.Column('spec', postgresql.JSONB, nullable=True),  # AnalyticsSpec
        sa.Column('sql_query', sa.Text, nullable=True),
        sa.Column('result_data', postgresql.JSONB, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    
    # Indexes for analytics_jobs
    op.create_index('idx_analytics_jobs_tenant_user', 'analytics_jobs', ['tenant_id', 'user_id'])
    op.create_index('idx_analytics_jobs_status', 'analytics_jobs', ['status'])
    op.create_index('idx_analytics_jobs_created', 'analytics_jobs', ['created_at'])
    
    # 5. Create analytics_cache table
    op.create_table(
        'analytics_cache',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('spec_hash', sa.String(64), nullable=False),  # SHA256 of AnalyticsSpec
        sa.Column('spec', postgresql.JSONB, nullable=False),
        sa.Column('sql_query', sa.Text, nullable=False),
        sa.Column('result_data', postgresql.JSONB, nullable=False),
        sa.Column('row_count', sa.Integer, nullable=False),
        sa.Column('execution_time_ms', sa.Integer, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'spec_hash', name='uq_analytics_cache_tenant_hash'),
    )
    
    # Indexes for analytics_cache
    op.create_index('idx_analytics_cache_tenant_hash', 'analytics_cache', ['tenant_id', 'spec_hash'])
    op.create_index('idx_analytics_cache_expires', 'analytics_cache', ['expires_at'])
    
    # Enable Row Level Security (RLS) for tenant isolation
    op.execute('ALTER TABLE sprints ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE metrics_catalog ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE analytics_jobs ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE analytics_cache ENABLE ROW LEVEL SECURITY')
    
    # Create RLS policies
    op.execute("""
        CREATE POLICY sprints_tenant_isolation ON sprints
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY metrics_catalog_tenant_isolation ON metrics_catalog
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY analytics_jobs_tenant_isolation ON analytics_jobs
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)
    
    op.execute("""
        CREATE POLICY analytics_cache_tenant_isolation ON analytics_cache
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute('DROP POLICY IF EXISTS analytics_cache_tenant_isolation ON analytics_cache')
    op.execute('DROP POLICY IF EXISTS analytics_jobs_tenant_isolation ON analytics_jobs')
    op.execute('DROP POLICY IF EXISTS metrics_catalog_tenant_isolation ON metrics_catalog')
    op.execute('DROP POLICY IF EXISTS sprints_tenant_isolation ON sprints')
    
    # Drop tables in reverse order
    op.drop_table('analytics_cache')
    op.drop_table('analytics_jobs')
    op.drop_table('metrics_catalog')
    op.drop_table('sprint_issues')
    op.drop_table('sprints')

