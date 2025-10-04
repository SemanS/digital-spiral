"""Add materialized views for analytics

Revision ID: 007_add_materialized_views
Revises: 006_add_analytics_tables
Create Date: 2025-10-04 01:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '007_add_materialized_views'
down_revision = '006_add_analytics_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create materialized view for sprint stats with z-scores
    op.execute("""
        CREATE MATERIALIZED VIEW mv_sprint_stats_enriched AS
        WITH sprint_metrics AS (
            SELECT
                s.id AS sprint_id,
                s.tenant_id,
                s.instance_id,
                s.name AS sprint_name,
                s.state,
                s.start_date,
                s.end_date,
                s.complete_date,
                
                -- Basic counts
                COUNT(DISTINCT si.issue_id) AS total_issues,
                COUNT(DISTINCT CASE WHEN si.completed THEN si.issue_id END) AS completed_issues,
                COUNT(DISTINCT CASE WHEN si.removed_at IS NOT NULL THEN si.issue_id END) AS removed_issues,
                
                -- Story points
                COALESCE(SUM(si.story_points), 0) AS total_points,
                COALESCE(SUM(CASE WHEN si.completed THEN si.story_points END), 0) AS completed_points,
                
                -- Velocity (completed points)
                COALESCE(SUM(CASE WHEN si.completed THEN si.story_points END), 0) AS velocity,
                
                -- Commitment accuracy (completed / total)
                CASE 
                    WHEN SUM(si.story_points) > 0 
                    THEN COALESCE(SUM(CASE WHEN si.completed THEN si.story_points END), 0) / SUM(si.story_points)
                    ELSE 0
                END AS commitment_accuracy,
                
                -- Sprint duration
                CASE 
                    WHEN s.start_date IS NOT NULL AND s.end_date IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (s.end_date - s.start_date)) / 86400
                    ELSE NULL
                END AS duration_days
                
            FROM sprints s
            LEFT JOIN sprint_issues si ON s.id = si.sprint_id
            WHERE s.state = 'closed'  -- Only closed sprints for stats
            GROUP BY s.id, s.tenant_id, s.instance_id, s.name, s.state, 
                     s.start_date, s.end_date, s.complete_date
        ),
        tenant_stats AS (
            SELECT
                tenant_id,
                instance_id,
                
                -- Averages for z-score calculation
                AVG(velocity) AS avg_velocity,
                STDDEV(velocity) AS stddev_velocity,
                
                AVG(commitment_accuracy) AS avg_commitment_accuracy,
                STDDEV(commitment_accuracy) AS stddev_commitment_accuracy,
                
                AVG(total_issues) AS avg_total_issues,
                STDDEV(total_issues) AS stddev_total_issues
                
            FROM sprint_metrics
            GROUP BY tenant_id, instance_id
        )
        SELECT
            sm.*,
            
            -- Z-scores (how many standard deviations from mean)
            CASE 
                WHEN ts.stddev_velocity > 0 
                THEN (sm.velocity - ts.avg_velocity) / ts.stddev_velocity
                ELSE 0
            END AS velocity_z_score,
            
            CASE 
                WHEN ts.stddev_commitment_accuracy > 0 
                THEN (sm.commitment_accuracy - ts.avg_commitment_accuracy) / ts.stddev_commitment_accuracy
                ELSE 0
            END AS commitment_accuracy_z_score,
            
            CASE 
                WHEN ts.stddev_total_issues > 0 
                THEN (sm.total_issues - ts.avg_total_issues) / ts.stddev_total_issues
                ELSE 0
            END AS total_issues_z_score,
            
            -- Tenant averages for comparison
            ts.avg_velocity,
            ts.avg_commitment_accuracy,
            ts.avg_total_issues
            
        FROM sprint_metrics sm
        JOIN tenant_stats ts ON sm.tenant_id = ts.tenant_id AND sm.instance_id = ts.instance_id
    """)
    
    # Create indexes on materialized view
    op.execute("""
        CREATE INDEX idx_mv_sprint_stats_tenant_instance 
        ON mv_sprint_stats_enriched(tenant_id, instance_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_mv_sprint_stats_sprint_id 
        ON mv_sprint_stats_enriched(sprint_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_mv_sprint_stats_dates 
        ON mv_sprint_stats_enriched(start_date, end_date)
    """)
    
    # 2. Create materialized view for issue comment stats
    op.execute("""
        CREATE MATERIALIZED VIEW mv_issue_comment_stats AS
        SELECT
            i.id AS issue_id,
            i.tenant_id,
            i.instance_id,
            i.key AS issue_key,
            i.issue_type,
            i.priority,
            i.status,
            
            -- Comment counts
            COUNT(DISTINCT c.id) AS total_comments,
            COUNT(DISTINCT c.author_id) AS unique_commenters,
            
            -- Comment timing
            MIN(c.created_at) AS first_comment_at,
            MAX(c.created_at) AS last_comment_at,
            
            -- Time to first comment (from issue creation)
            CASE 
                WHEN MIN(c.created_at) IS NOT NULL
                THEN EXTRACT(EPOCH FROM (MIN(c.created_at) - i.created_at)) / 3600
                ELSE NULL
            END AS hours_to_first_comment,
            
            -- Average comment length
            AVG(LENGTH(c.body)) AS avg_comment_length,
            
            -- Comments per day (if issue has comments)
            CASE 
                WHEN COUNT(c.id) > 0 AND MAX(c.created_at) > MIN(c.created_at)
                THEN COUNT(c.id)::FLOAT / 
                     GREATEST(1, EXTRACT(EPOCH FROM (MAX(c.created_at) - MIN(c.created_at))) / 86400)
                ELSE 0
            END AS comments_per_day
            
        FROM issues i
        LEFT JOIN comments c ON i.id = c.issue_id
        GROUP BY i.id, i.tenant_id, i.instance_id, i.key, i.issue_type, 
                 i.priority, i.status, i.created_at
    """)
    
    # Create indexes on materialized view
    op.execute("""
        CREATE INDEX idx_mv_issue_comment_stats_tenant_instance 
        ON mv_issue_comment_stats(tenant_id, instance_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_mv_issue_comment_stats_issue_id 
        ON mv_issue_comment_stats(issue_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_mv_issue_comment_stats_issue_key 
        ON mv_issue_comment_stats(issue_key)
    """)


def downgrade() -> None:
    # Drop materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_issue_comment_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_sprint_stats_enriched")

