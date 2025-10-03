"""Audit log service for tracking all write operations."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.audit_log import AuditLog


class AuditLogService:
    """Service for creating and managing audit logs."""

    def __init__(self, session: AsyncSession):
        """Initialize the audit log service.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def log(
        self,
        tenant_id: UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        changes: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create an audit log entry.

        Args:
            tenant_id: Tenant ID
            action: Action performed (create, update, delete, etc.)
            resource_type: Type of resource (issue, instance, project, etc.)
            resource_id: ID or key of the resource
            changes: Dictionary with before/after values
            user_id: User who performed the action
            request_id: Request ID for tracing
            ip_address: Client IP address
            user_agent: Client user agent
            metadata: Additional metadata

        Returns:
            Created audit log entry
        """
        audit_log = AuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.session.add(audit_log)
        await self.session.flush()

        return audit_log

    async def log_create(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a create operation.

        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource
            resource_id: ID or key of the resource
            data: Created data
            user_id: User who performed the action
            request_id: Request ID for tracing
            metadata: Additional metadata

        Returns:
            Created audit log entry
        """
        changes = {"before": None, "after": data}
        return await self.log(
            tenant_id=tenant_id,
            action="create",
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata,
        )

    async def log_update(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        before: Dict[str, Any],
        after: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log an update operation.

        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource
            resource_id: ID or key of the resource
            before: Data before update
            after: Data after update
            user_id: User who performed the action
            request_id: Request ID for tracing
            metadata: Additional metadata

        Returns:
            Created audit log entry
        """
        changes = {"before": before, "after": after}
        return await self.log(
            tenant_id=tenant_id,
            action="update",
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata,
        )

    async def log_delete(
        self,
        tenant_id: UUID,
        resource_type: str,
        resource_id: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a delete operation.

        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource
            resource_id: ID or key of the resource
            data: Deleted data
            user_id: User who performed the action
            request_id: Request ID for tracing
            metadata: Additional metadata

        Returns:
            Created audit log entry
        """
        changes = {"before": data, "after": None}
        return await self.log(
            tenant_id=tenant_id,
            action="delete",
            resource_type=resource_type,
            resource_id=resource_id,
            changes=changes,
            user_id=user_id,
            request_id=request_id,
            metadata=metadata,
        )


__all__ = ["AuditLogService"]

