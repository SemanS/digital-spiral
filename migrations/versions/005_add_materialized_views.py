"""Add materialized views for analytics

Revision ID: 005_materialized_views
Revises: 004_row_level_security
Create Date: 2025-10-03 16:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '005_materialized_views'
down_revision = '004_row_level_security'
branch_labels = None
depends_on = None


def upgrade():
    """Create materialized views for analytics and reporting."""
    
    # ============================================================================
    # 1. Issue Statistics by Project
    # ============================================================================
    
    op.execute("""
        CREATE MATERIALIZED VIEW mv_issue_stats_by_project AS
        SELECT 
            i.tenant_id,
            i.instance_id,
            i.project_id,
            i.project_key,
            p.name AS project_name,
            COUNT(*) AS total_issues,
            COUNT(*) FILTER (WHERE i.status_category = 'To Do') AS todo_count,
            COUNT(*) FILTER (WHERE i.status_category = 'In Progress') AS in_progress_count,
            COUNT(*) FILTER (WHERE i.status_category = 'Done') AS done_count,
            COUNT(*) FILTER (WHERE i.issue_type = 'Bug') AS bug_count,
            COUNT(*) FILTER (WHERE i.issue_type = 'Story') AS story_count,
            COUNT(*) FILTER (WHERE i.issue_type = 'Task') AS task_count,
            COUNT(*) FILTER (WHERE i.issue_type = 'Epic') AS epic_count,
            COUNT(*) FILTER (WHERE i.priority = 'Highest') AS highest_priority_count,
            COUNT(*) FILTER (WHERE i.priority = 'High') AS high_priority_count,
            COUNT(*) FILTER (WHERE i.priority = 'Medium') AS medium_priority_count,
            COUNT(*) FILTER (WHERE i.priority = 'Low') AS low_priority_count,
            COUNT(*) FILTER (WHERE i.priority = 'Lowest') AS lowest_priority_count,
            COUNT(*) FILTER (WHERE i.assignee_account_id IS NULL) AS unassigned_count,
            COUNT(*) FILTER (WHERE i.parent_id IS NOT NULL) AS subtask_count,
            AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.jira_created_at)) / 86400) 
                FILTER (WHERE i.resolved_at IS NOT NULL) AS avg_resolution_days,
            MAX(i.jira_updated_at) AS last_updated_at,
            NOW() AS refreshed_at
        FROM issues i
        LEFT JOIN projects p ON i.project_id = p.id
        GROUP BY 
            i.tenant_id,
            i.instance_id,
            i.project_id,
            i.project_key,
            p.name
    """)
    
    # Create indexes on materialized view
    op.execute("""
        CREATE UNIQUE INDEX ix_mv_issue_stats_by_project_pk 
        ON mv_issue_stats_by_project (tenant_id, instance_id, project_id)
    """)
    
    op.execute("""
        CREATE INDEX ix_mv_issue_stats_by_project_tenant 
        ON mv_issue_stats_by_project (tenant_id)
    """)
    
    # ============================================================================
    # 2. Issue Statistics by Assignee
    # ============================================================================
    
    op.execute("""
        CREATE MATERIALIZED VIEW mv_issue_stats_by_assignee AS
        SELECT 
            i.tenant_id,
            i.instance_id,
            i.assignee_account_id,
            u.display_name AS assignee_name,
            u.email_address AS assignee_email,
            COUNT(*) AS total_assigned,
            COUNT(*) FILTER (WHERE i.status_category = 'To Do') AS todo_count,
            COUNT(*) FILTER (WHERE i.status_category = 'In Progress') AS in_progress_count,
            COUNT(*) FILTER (WHERE i.status_category = 'Done') AS done_count,
            COUNT(*) FILTER (WHERE i.issue_type = 'Bug') AS bug_count,
            COUNT(*) FILTER (WHERE i.priority IN ('Highest', 'High')) AS high_priority_count,
            AVG(EXTRACT(EPOCH FROM (i.resolved_at - i.jira_created_at)) / 86400) 
                FILTER (WHERE i.resolved_at IS NOT NULL) AS avg_resolution_days,
            MAX(i.jira_updated_at) AS last_updated_at,
            NOW() AS refreshed_at
        FROM issues i
        LEFT JOIN users u ON i.assignee_account_id = u.account_id AND i.instance_id = u.instance_id
        WHERE i.assignee_account_id IS NOT NULL
        GROUP BY 
            i.tenant_id,
            i.instance_id,
            i.assignee_account_id,
            u.display_name,
            u.email_address
    """)
    
    # Create indexes
    op.execute("""
        CREATE UNIQUE INDEX ix_mv_issue_stats_by_assignee_pk 
        ON mv_issue_stats_by_assignee (tenant_id, instance_id, assignee_account_id)
    """)
    
    op.execute("""
        CREATE INDEX ix_mv_issue_stats_by_assignee_tenant 
        ON mv_issue_stats_by_assignee (tenant_id)
    """)
    
    # ============================================================================
    # 3. Issue Activity Timeline
    # ============================================================================
    
    op.execute("""
        CREATE MATERIALIZED VIEW mv_issue_activity_timeline AS
        SELECT 
            i.tenant_id,
            i.instance_id,
            i.project_id,
            DATE(i.jira_created_at) AS activity_date,
            COUNT(*) AS issues_created,
            COUNT(*) FILTER (WHERE i.resolved_at IS NOT NULL 
                AND DATE(i.resolved_at) = DATE(i.jira_created_at)) AS issues_resolved_same_day,
            COUNT(*) FILTER (WHERE i.issue_type = 'Bug') AS bugs_created,
            COUNT(*) FILTER (WHERE i.issue_type = 'Story') AS stories_created,
            NOW() AS refreshed_at
        FROM issues i
        WHERE i.jira_created_at IS NOT NULL
        GROUP BY 
            i.tenant_id,
            i.instance_id,
            i.project_id,
            DATE(i.jira_created_at)
    """)
    
    # Create indexes
    op.execute("""
        CREATE INDEX ix_mv_issue_activity_timeline_tenant_date 
        ON mv_issue_activity_timeline (tenant_id, activity_date DESC)
    """)
    
    op.execute("""
        CREATE INDEX ix_mv_issue_activity_timeline_project_date 
        ON mv_issue_activity_timeline (project_id, activity_date DESC)
    """)
    
    # ============================================================================
    # 4. Issue Label Statistics
    # ============================================================================
    
    op.execute("""
        CREATE MATERIALIZED VIEW mv_issue_label_stats AS
        SELECT 
            i.tenant_id,
            i.instance_id,
            i.project_id,
            unnest(i.labels) AS label,
            COUNT(*) AS issue_count,
            COUNT(*) FILTER (WHERE i.status_category = 'Done') AS done_count,
            COUNT(*) FILTER (WHERE i.status_category IN ('To Do', 'In Progress')) AS active_count,
            NOW() AS refreshed_at
        FROM issues i
        WHERE array_length(i.labels, 1) > 0
        GROUP BY 
            i.tenant_id,
            i.instance_id,
            i.project_id,
            unnest(i.labels)
    """)
    
    # Create indexes
    op.execute("""
        CREATE INDEX ix_mv_issue_label_stats_tenant_label 
        ON mv_issue_label_stats (tenant_id, label)
    """)
    
    op.execute("""
        CREATE INDEX ix_mv_issue_label_stats_project_label 
        ON mv_issue_label_stats (project_id, label)
    """)
    
    # ============================================================================
    # 5. Comment Activity Statistics
    # ============================================================================
    
    op.execute("""
        CREATE MATERIALIZED VIEW mv_comment_activity_stats AS
        SELECT 
            c.tenant_id,
            c.instance_id,
            c.issue_id,
            i.issue_key,
            i.project_id,
            COUNT(*) AS total_comments,
            COUNT(DISTINCT c.author_account_id) AS unique_commenters,
            MIN(c.jira_created_at) AS first_comment_at,
            MAX(c.jira_created_at) AS last_comment_at,
            AVG(LENGTH(c.body)) AS avg_comment_length,
            NOW() AS refreshed_at
        FROM comments c
        JOIN issues i ON c.issue_id = i.id
        GROUP BY 
            c.tenant_id,
            c.instance_id,
            c.issue_id,
            i.issue_key,
            i.project_id
    """)
    
    # Create indexes
    op.execute("""
        CREATE UNIQUE INDEX ix_mv_comment_activity_stats_pk 
        ON mv_comment_activity_stats (tenant_id, instance_id, issue_id)
    """)
    
    op.execute("""
        CREATE INDEX ix_mv_comment_activity_stats_project 
        ON mv_comment_activity_stats (project_id)
    """)
    
    # ============================================================================
    # 6. Changelog Activity Statistics
    # ============================================================================
    
    op.execute("""
        CREATE MATERIALIZED VIEW mv_changelog_activity_stats AS
        SELECT 
            cl.tenant_id,
            cl.instance_id,
            cl.issue_id,
            i.issue_key,
            i.project_id,
            COUNT(*) AS total_changes,
            COUNT(DISTINCT cl.author_account_id) AS unique_changers,
            MIN(cl.jira_created_at) AS first_change_at,
            MAX(cl.jira_created_at) AS last_change_at,
            COUNT(*) FILTER (
                WHERE EXISTS (
                    SELECT 1 FROM jsonb_array_elements(cl.items) AS item
                    WHERE item->>'field' = 'status'
                )
            ) AS status_changes,
            NOW() AS refreshed_at
        FROM changelogs cl
        JOIN issues i ON cl.issue_id = i.id
        GROUP BY 
            cl.tenant_id,
            cl.instance_id,
            cl.issue_id,
            i.issue_key,
            i.project_id
    """)
    
    # Create indexes
    op.execute("""
        CREATE UNIQUE INDEX ix_mv_changelog_activity_stats_pk 
        ON mv_changelog_activity_stats (tenant_id, instance_id, issue_id)
    """)
    
    op.execute("""
        CREATE INDEX ix_mv_changelog_activity_stats_project 
        ON mv_changelog_activity_stats (project_id)
    """)
    
    # ============================================================================
    # Create function to refresh all materialized views
    # ============================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_issue_stats_by_project;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_issue_stats_by_assignee;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_issue_activity_timeline;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_issue_label_stats;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_comment_activity_stats;
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_changelog_activity_stats;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade():
    """Drop materialized views."""
    
    # Drop refresh function
    op.execute("DROP FUNCTION IF EXISTS refresh_all_materialized_views()")
    
    # Drop materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_changelog_activity_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_comment_activity_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_issue_label_stats")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_issue_activity_timeline")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_issue_stats_by_assignee")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_issue_stats_by_project")

