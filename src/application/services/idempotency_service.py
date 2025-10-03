"""Idempotency service for ensuring idempotent write operations."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.idempotency_key import IdempotencyKey


class IdempotencyService:
    """Service for handling idempotent write operations."""

    def __init__(self, session: AsyncSession, ttl_hours: int = 24):
        """Initialize the idempotency service.

        Args:
            session: SQLAlchemy async session
            ttl_hours: Time-to-live for idempotency keys in hours (default: 24)
        """
        self.session = session
        self.ttl_hours = ttl_hours

    async def check(
        self,
        tenant_id: UUID,
        operation: str,
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """Check if an operation was already executed.

        Args:
            tenant_id: Tenant ID
            operation: Operation type (e.g., 'create_issue', 'update_issue')
            key: Idempotency key

        Returns:
            Result of the previous operation if it exists and hasn't expired, None otherwise
        """
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.tenant_id == tenant_id,
            IdempotencyKey.operation == operation,
            IdempotencyKey.key == key,
            IdempotencyKey.expires_at > datetime.now(timezone.utc),
        )

        result = await self.session.execute(stmt)
        idempotency_key = result.scalar_one_or_none()

        if idempotency_key:
            if idempotency_key.status == "completed":
                return idempotency_key.result
            elif idempotency_key.status == "failed":
                # Return the error so the client knows it failed before
                return {"error": idempotency_key.error}

        return None

    async def store(
        self,
        tenant_id: UUID,
        operation: str,
        key: str,
        result: Dict[str, Any],
        status: str = "completed",
        error: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> IdempotencyKey:
        """Store the result of an operation.

        Args:
            tenant_id: Tenant ID
            operation: Operation type
            key: Idempotency key
            result: Result of the operation
            status: Status of the operation (completed, failed, processing)
            error: Error details if the operation failed
            request_id: Request ID for tracing

        Returns:
            Created idempotency key entry
        """
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.ttl_hours)

        idempotency_key = IdempotencyKey(
            id=uuid4(),
            tenant_id=tenant_id,
            key=key,
            operation=operation,
            result=result,
            status=status,
            error=error,
            expires_at=expires_at,
            request_id=request_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(idempotency_key)
        await self.session.flush()

        return idempotency_key

    async def check_and_store(
        self,
        tenant_id: UUID,
        operation: str,
        key: str,
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """Check if operation was executed and prepare for storing result.

        This is a convenience method that combines check and prepares for store.

        Args:
            tenant_id: Tenant ID
            operation: Operation type
            key: Idempotency key

        Returns:
            Tuple of (is_duplicate, previous_result)
            - is_duplicate: True if the operation was already executed
            - previous_result: Result of the previous operation if it exists
        """
        previous_result = await self.check(tenant_id, operation, key)

        if previous_result is not None:
            return True, previous_result

        return False, None

    async def cleanup_expired(self) -> int:
        """Clean up expired idempotency keys.

        This should be called periodically (e.g., via a cron job).

        Returns:
            Number of deleted keys
        """
        from sqlalchemy import delete

        stmt = delete(IdempotencyKey).where(
            IdempotencyKey.expires_at <= datetime.now(timezone.utc)
        )

        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount


__all__ = ["IdempotencyService"]

