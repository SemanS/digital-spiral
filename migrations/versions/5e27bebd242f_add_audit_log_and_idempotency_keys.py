"""add_audit_log_and_idempotency_keys

Revision ID: 5e27bebd242f
Revises: 005_materialized_views
Create Date: 2025-10-03 21:18:55.015734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5e27bebd242f'
down_revision: Union[str, None] = '005_materialized_views'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('changes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for audit_logs
    op.create_index('ix_audit_logs_tenant_id', 'audit_logs', ['tenant_id'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_request_id', 'audit_logs', ['request_id'])
    op.create_index('ix_audit_logs_tenant_timestamp', 'audit_logs', ['tenant_id', 'created_at'])
    op.create_index('ix_audit_logs_tenant_resource', 'audit_logs', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('ix_audit_logs_tenant_action', 'audit_logs', ['tenant_id', 'action'])
    op.create_index('ix_audit_logs_user_timestamp', 'audit_logs', ['user_id', 'created_at'])
    op.create_index('ix_audit_logs_changes', 'audit_logs', ['changes'], postgresql_using='gin')
    op.create_index('ix_audit_logs_metadata', 'audit_logs', ['metadata'], postgresql_using='gin')

    # Create idempotency_keys table
    op.create_table(
        'idempotency_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('operation', sa.String(length=100), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for idempotency_keys
    op.create_index('ix_idempotency_keys_tenant_id', 'idempotency_keys', ['tenant_id'])
    op.create_index('ix_idempotency_keys_key', 'idempotency_keys', ['key'])
    op.create_index('ix_idempotency_keys_tenant_operation_key', 'idempotency_keys',
                    ['tenant_id', 'operation', 'key'], unique=True)
    op.create_index('ix_idempotency_keys_expires_at', 'idempotency_keys', ['expires_at'])
    op.create_index('ix_idempotency_keys_tenant_created', 'idempotency_keys', ['tenant_id', 'created_at'])


def downgrade() -> None:
    # Drop idempotency_keys table and indexes
    op.drop_index('ix_idempotency_keys_tenant_created', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_expires_at', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_tenant_operation_key', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_key', table_name='idempotency_keys')
    op.drop_index('ix_idempotency_keys_tenant_id', table_name='idempotency_keys')
    op.drop_table('idempotency_keys')

    # Drop audit_logs table and indexes
    op.drop_index('ix_audit_logs_metadata', table_name='audit_logs')
    op.drop_index('ix_audit_logs_changes', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_resource', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_request_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_resource_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_tenant_id', table_name='audit_logs')
    op.drop_table('audit_logs')
