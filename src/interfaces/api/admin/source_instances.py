"""Admin API endpoints for managing source instances."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.adapters import SourceType, create_adapter
from src.infrastructure.database.models.jira_instance import JiraInstance
from src.infrastructure.database.session import get_session

router = APIRouter(prefix="/admin/source-instances", tags=["admin"])


# Schemas
class SourceInstanceCreate(BaseModel):
    """Schema for creating a source instance."""

    name: str = Field(..., description="Instance name")
    source_type: SourceType = Field(..., description="Source type (jira, github, etc.)")
    base_url: str = Field(..., description="Base URL for the source API")
    auth_config: dict = Field(..., description="Authentication configuration")
    is_active: bool = Field(default=True, description="Whether instance is active")


class SourceInstanceUpdate(BaseModel):
    """Schema for updating a source instance."""

    name: str | None = None
    base_url: str | None = None
    auth_config: dict | None = None
    is_active: bool | None = None


class SourceInstanceResponse(BaseModel):
    """Schema for source instance response."""

    id: UUID
    tenant_id: UUID
    name: str
    source_type: SourceType
    base_url: str
    is_active: bool
    connection_status: str | None = None
    last_sync_at: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ConnectionTestResponse(BaseModel):
    """Schema for connection test response."""

    success: bool
    message: str
    details: dict | None = None


# Endpoints
@router.post(
    "",
    response_model=SourceInstanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create source instance",
    description="Create a new source instance (Jira, GitHub, etc.)",
)
async def create_source_instance(
    data: SourceInstanceCreate,
    tenant_id: UUID,  # TODO: Get from auth
    session: AsyncSession = Depends(get_session),
):
    """Create a new source instance."""
    # Create instance record
    instance = JiraInstance(
        tenant_id=tenant_id,
        name=data.name,
        base_url=data.base_url,
        # TODO: Encrypt auth_config before storing
        auth_config=data.auth_config,
        is_active=data.is_active,
    )
    
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    
    return SourceInstanceResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        name=instance.name,
        source_type=SourceType.JIRA,  # TODO: Get from instance
        base_url=instance.base_url,
        is_active=instance.is_active,
        connection_status=None,
        last_sync_at=None,
        created_at=instance.created_at.isoformat(),
        updated_at=instance.updated_at.isoformat(),
    )


@router.get(
    "",
    response_model=List[SourceInstanceResponse],
    summary="List source instances",
    description="List all source instances for the tenant",
)
async def list_source_instances(
    tenant_id: UUID,  # TODO: Get from auth
    source_type: SourceType | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List all source instances."""
    stmt = select(JiraInstance).where(JiraInstance.tenant_id == tenant_id)
    
    if is_active is not None:
        stmt = stmt.where(JiraInstance.is_active == is_active)
    
    result = await session.execute(stmt)
    instances = result.scalars().all()
    
    return [
        SourceInstanceResponse(
            id=instance.id,
            tenant_id=instance.tenant_id,
            name=instance.name,
            source_type=SourceType.JIRA,  # TODO: Get from instance
            base_url=instance.base_url,
            is_active=instance.is_active,
            connection_status=None,
            last_sync_at=None,
            created_at=instance.created_at.isoformat(),
            updated_at=instance.updated_at.isoformat(),
        )
        for instance in instances
    ]


@router.get(
    "/{instance_id}",
    response_model=SourceInstanceResponse,
    summary="Get source instance",
    description="Get a specific source instance by ID",
)
async def get_source_instance(
    instance_id: UUID,
    tenant_id: UUID,  # TODO: Get from auth
    session: AsyncSession = Depends(get_session),
):
    """Get a source instance by ID."""
    stmt = select(JiraInstance).where(
        JiraInstance.id == instance_id,
        JiraInstance.tenant_id == tenant_id,
    )
    
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source instance not found",
        )
    
    return SourceInstanceResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        name=instance.name,
        source_type=SourceType.JIRA,  # TODO: Get from instance
        base_url=instance.base_url,
        is_active=instance.is_active,
        connection_status=None,
        last_sync_at=None,
        created_at=instance.created_at.isoformat(),
        updated_at=instance.updated_at.isoformat(),
    )


@router.patch(
    "/{instance_id}",
    response_model=SourceInstanceResponse,
    summary="Update source instance",
    description="Update a source instance",
)
async def update_source_instance(
    instance_id: UUID,
    data: SourceInstanceUpdate,
    tenant_id: UUID,  # TODO: Get from auth
    session: AsyncSession = Depends(get_session),
):
    """Update a source instance."""
    stmt = select(JiraInstance).where(
        JiraInstance.id == instance_id,
        JiraInstance.tenant_id == tenant_id,
    )
    
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source instance not found",
        )
    
    # Update fields
    if data.name is not None:
        instance.name = data.name
    if data.base_url is not None:
        instance.base_url = data.base_url
    if data.auth_config is not None:
        # TODO: Encrypt auth_config
        instance.auth_config = data.auth_config
    if data.is_active is not None:
        instance.is_active = data.is_active
    
    await session.commit()
    await session.refresh(instance)
    
    return SourceInstanceResponse(
        id=instance.id,
        tenant_id=instance.tenant_id,
        name=instance.name,
        source_type=SourceType.JIRA,  # TODO: Get from instance
        base_url=instance.base_url,
        is_active=instance.is_active,
        connection_status=None,
        last_sync_at=None,
        created_at=instance.created_at.isoformat(),
        updated_at=instance.updated_at.isoformat(),
    )


@router.delete(
    "/{instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete source instance",
    description="Delete a source instance",
)
async def delete_source_instance(
    instance_id: UUID,
    tenant_id: UUID,  # TODO: Get from auth
    session: AsyncSession = Depends(get_session),
):
    """Delete a source instance."""
    stmt = select(JiraInstance).where(
        JiraInstance.id == instance_id,
        JiraInstance.tenant_id == tenant_id,
    )
    
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source instance not found",
        )
    
    await session.delete(instance)
    await session.commit()


@router.post(
    "/{instance_id}/test-connection",
    response_model=ConnectionTestResponse,
    summary="Test connection",
    description="Test connection to a source instance",
)
async def test_connection(
    instance_id: UUID,
    tenant_id: UUID,  # TODO: Get from auth
    session: AsyncSession = Depends(get_session),
):
    """Test connection to a source instance."""
    stmt = select(JiraInstance).where(
        JiraInstance.id == instance_id,
        JiraInstance.tenant_id == tenant_id,
    )
    
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()
    
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source instance not found",
        )
    
    try:
        # Create adapter and test connection
        adapter = create_adapter(
            source_type=SourceType.JIRA,  # TODO: Get from instance
            instance_id=instance.id,
            base_url=instance.base_url,
            auth_config=instance.auth_config,
        )
        
        success = await adapter.test_connection()
        
        if success:
            return ConnectionTestResponse(
                success=True,
                message="Connection successful",
                details={"instance_id": str(instance.id)},
            )
        else:
            return ConnectionTestResponse(
                success=False,
                message="Connection failed",
                details={"instance_id": str(instance.id)},
            )
    
    except Exception as e:
        return ConnectionTestResponse(
            success=False,
            message=f"Connection error: {str(e)}",
            details={"instance_id": str(instance.id), "error": str(e)},
        )


__all__ = ["router"]

