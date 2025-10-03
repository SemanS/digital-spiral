"""Unit tests for AuditLogService."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from src.application.services.audit_log_service import AuditLogService
from src.infrastructure.database.models.audit_log import AuditLog


@pytest.fixture
def tenant_id():
    """Create a test tenant ID."""
    return uuid4()


@pytest.fixture
def audit_service(db_session):
    """Create an audit log service."""
    return AuditLogService(db_session)


class TestAuditLogService:
    """Tests for AuditLogService."""

    async def test_log_creates_entry(self, audit_service, tenant_id, db_session):
        """Test that log creates an audit entry."""
        audit_log = await audit_service.log(
            tenant_id=tenant_id,
            action="test_action",
            resource_type="test_resource",
            resource_id="test-123",
            changes={"before": None, "after": {"field": "value"}},
            user_id="test@example.com",
            request_id="req-123",
        )

        assert audit_log.id is not None
        assert audit_log.tenant_id == tenant_id
        assert audit_log.action == "test_action"
        assert audit_log.resource_type == "test_resource"
        assert audit_log.resource_id == "test-123"
        assert audit_log.user_id == "test@example.com"
        assert audit_log.request_id == "req-123"
        assert audit_log.changes == {"before": None, "after": {"field": "value"}}

    async def test_log_create(self, audit_service, tenant_id, db_session):
        """Test log_create method."""
        data = {"summary": "Test issue", "status": "Open"}
        
        audit_log = await audit_service.log_create(
            tenant_id=tenant_id,
            resource_type="issue",
            resource_id="PROJ-123",
            data=data,
            user_id="test@example.com",
        )

        assert audit_log.action == "create"
        assert audit_log.changes["before"] is None
        assert audit_log.changes["after"] == data

    async def test_log_update(self, audit_service, tenant_id, db_session):
        """Test log_update method."""
        before = {"summary": "Old summary", "status": "Open"}
        after = {"summary": "New summary", "status": "In Progress"}
        
        audit_log = await audit_service.log_update(
            tenant_id=tenant_id,
            resource_type="issue",
            resource_id="PROJ-123",
            before=before,
            after=after,
            user_id="test@example.com",
        )

        assert audit_log.action == "update"
        assert audit_log.changes["before"] == before
        assert audit_log.changes["after"] == after

    async def test_log_delete(self, audit_service, tenant_id, db_session):
        """Test log_delete method."""
        data = {"summary": "Deleted issue", "status": "Done"}
        
        audit_log = await audit_service.log_delete(
            tenant_id=tenant_id,
            resource_type="issue",
            resource_id="PROJ-123",
            data=data,
            user_id="test@example.com",
        )

        assert audit_log.action == "delete"
        assert audit_log.changes["before"] == data
        assert audit_log.changes["after"] is None

    async def test_log_with_metadata(self, audit_service, tenant_id, db_session):
        """Test logging with metadata."""
        metadata = {"instance_id": str(uuid4()), "tool_name": "jira.create_issue"}
        
        audit_log = await audit_service.log(
            tenant_id=tenant_id,
            action="create",
            resource_type="issue",
            resource_id="PROJ-123",
            changes={},
            metadata=metadata,
        )

        assert audit_log.metadata == metadata

    async def test_log_with_ip_and_user_agent(self, audit_service, tenant_id, db_session):
        """Test logging with IP address and user agent."""
        audit_log = await audit_service.log(
            tenant_id=tenant_id,
            action="create",
            resource_type="issue",
            resource_id="PROJ-123",
            changes={},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )

        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.user_agent == "Mozilla/5.0"

    async def test_multiple_logs_for_same_resource(self, audit_service, tenant_id, db_session):
        """Test creating multiple audit logs for the same resource."""
        # Create
        await audit_service.log_create(
            tenant_id=tenant_id,
            resource_type="issue",
            resource_id="PROJ-123",
            data={"summary": "Test"},
        )

        # Update
        await audit_service.log_update(
            tenant_id=tenant_id,
            resource_type="issue",
            resource_id="PROJ-123",
            before={"summary": "Test"},
            after={"summary": "Updated"},
        )

        # Delete
        await audit_service.log_delete(
            tenant_id=tenant_id,
            resource_type="issue",
            resource_id="PROJ-123",
            data={"summary": "Updated"},
        )

        # Query all logs for this resource
        stmt = select(AuditLog).where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.resource_id == "PROJ-123",
        ).order_by(AuditLog.created_at)

        result = await db_session.execute(stmt)
        logs = result.scalars().all()

        assert len(logs) == 3
        assert logs[0].action == "create"
        assert logs[1].action == "update"
        assert logs[2].action == "delete"

