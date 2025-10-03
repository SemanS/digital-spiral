"""Unit tests for IdempotencyService."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.application.services.idempotency_service import IdempotencyService
from src.infrastructure.database.models.idempotency_key import IdempotencyKey


@pytest.fixture
def tenant_id():
    """Create a test tenant ID."""
    return uuid4()


@pytest.fixture
def idempotency_service(db_session):
    """Create an idempotency service."""
    return IdempotencyService(db_session, ttl_hours=24)


class TestIdempotencyService:
    """Tests for IdempotencyService."""

    async def test_check_returns_none_for_new_key(
        self, idempotency_service, tenant_id
    ):
        """Test that check returns None for a new key."""
        result = await idempotency_service.check(
            tenant_id=tenant_id,
            operation="create_issue",
            key="new-key-123",
        )

        assert result is None

    async def test_store_creates_entry(self, idempotency_service, tenant_id, db_session):
        """Test that store creates an idempotency entry."""
        result_data = {"issue_key": "PROJ-123", "id": str(uuid4())}
        
        entry = await idempotency_service.store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="test-key-123",
            result=result_data,
            status="completed",
        )

        assert entry.id is not None
        assert entry.tenant_id == tenant_id
        assert entry.operation == "create_issue"
        assert entry.key == "test-key-123"
        assert entry.result == result_data
        assert entry.status == "completed"
        assert entry.expires_at > datetime.now(timezone.utc)

    async def test_check_returns_stored_result(
        self, idempotency_service, tenant_id, db_session
    ):
        """Test that check returns previously stored result."""
        result_data = {"issue_key": "PROJ-123"}
        
        # Store result
        await idempotency_service.store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="test-key-123",
            result=result_data,
        )
        await db_session.commit()

        # Check should return the stored result
        result = await idempotency_service.check(
            tenant_id=tenant_id,
            operation="create_issue",
            key="test-key-123",
        )

        assert result == result_data

    async def test_check_and_store_detects_duplicate(
        self, idempotency_service, tenant_id, db_session
    ):
        """Test that check_and_store detects duplicates."""
        result_data = {"issue_key": "PROJ-123"}
        
        # First call - not a duplicate
        is_duplicate, previous_result = await idempotency_service.check_and_store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="test-key-123",
        )

        assert is_duplicate is False
        assert previous_result is None

        # Store the result
        await idempotency_service.store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="test-key-123",
            result=result_data,
        )
        await db_session.commit()

        # Second call - should be a duplicate
        is_duplicate, previous_result = await idempotency_service.check_and_store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="test-key-123",
        )

        assert is_duplicate is True
        assert previous_result == result_data

    async def test_different_operations_same_key(
        self, idempotency_service, tenant_id, db_session
    ):
        """Test that same key for different operations are independent."""
        # Store for create_issue
        await idempotency_service.store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="same-key",
            result={"operation": "create"},
        )

        # Store for update_issue
        await idempotency_service.store(
            tenant_id=tenant_id,
            operation="update_issue",
            key="same-key",
            result={"operation": "update"},
        )

        await db_session.commit()

        # Check create_issue
        result1 = await idempotency_service.check(
            tenant_id=tenant_id,
            operation="create_issue",
            key="same-key",
        )

        # Check update_issue
        result2 = await idempotency_service.check(
            tenant_id=tenant_id,
            operation="update_issue",
            key="same-key",
        )

        assert result1["operation"] == "create"
        assert result2["operation"] == "update"

    async def test_different_tenants_same_key(
        self, idempotency_service, db_session
    ):
        """Test that same key for different tenants are independent."""
        tenant1 = uuid4()
        tenant2 = uuid4()

        # Store for tenant1
        await idempotency_service.store(
            tenant_id=tenant1,
            operation="create_issue",
            key="same-key",
            result={"tenant": "1"},
        )

        # Store for tenant2
        await idempotency_service.store(
            tenant_id=tenant2,
            operation="create_issue",
            key="same-key",
            result={"tenant": "2"},
        )

        await db_session.commit()

        # Check tenant1
        result1 = await idempotency_service.check(
            tenant_id=tenant1,
            operation="create_issue",
            key="same-key",
        )

        # Check tenant2
        result2 = await idempotency_service.check(
            tenant_id=tenant2,
            operation="create_issue",
            key="same-key",
        )

        assert result1["tenant"] == "1"
        assert result2["tenant"] == "2"

    async def test_store_with_error(self, idempotency_service, tenant_id, db_session):
        """Test storing a failed operation."""
        error_data = {"code": "validation_error", "message": "Invalid input"}
        
        entry = await idempotency_service.store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="error-key",
            result={},
            status="failed",
            error=error_data,
        )

        assert entry.status == "failed"
        assert entry.error == error_data

    async def test_check_returns_error_for_failed_operation(
        self, idempotency_service, tenant_id, db_session
    ):
        """Test that check returns error for failed operations."""
        error_data = {"code": "validation_error", "message": "Invalid input"}
        
        await idempotency_service.store(
            tenant_id=tenant_id,
            operation="create_issue",
            key="error-key",
            result={},
            status="failed",
            error=error_data,
        )
        await db_session.commit()

        result = await idempotency_service.check(
            tenant_id=tenant_id,
            operation="create_issue",
            key="error-key",
        )

        assert result == {"error": error_data}

    async def test_expired_keys_not_returned(
        self, idempotency_service, tenant_id, db_session
    ):
        """Test that expired keys are not returned."""
        # Create an entry that's already expired
        from src.infrastructure.database.models.idempotency_key import IdempotencyKey
        
        expired_entry = IdempotencyKey(
            id=uuid4(),
            tenant_id=tenant_id,
            key="expired-key",
            operation="create_issue",
            result={"data": "old"},
            status="completed",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        db_session.add(expired_entry)
        await db_session.commit()

        # Check should return None for expired key
        result = await idempotency_service.check(
            tenant_id=tenant_id,
            operation="create_issue",
            key="expired-key",
        )

        assert result is None

