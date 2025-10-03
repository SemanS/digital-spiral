"""
Jira Instances API Router

This module provides REST API endpoints for managing Jira instances.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from sqlalchemy.orm import Session

from src.infrastructure.database.session import get_db
from src.infrastructure.database.models import JiraInstance, Tenant

router = APIRouter(prefix="/api/instances", tags=["instances"])


# ============================================================================
# Models
# ============================================================================

class InstanceBase(BaseModel):
    """Base model for Jira instance"""
    name: str = Field(..., min_length=1, max_length=100)
    base_url: str = Field(..., alias="baseUrl", description="Jira base URL (e.g., https://company.atlassian.net)")
    auth_method: str = Field(..., alias="authMethod", description="Authentication method: 'api_token' or 'oauth'")
    email: Optional[str] = Field(None, description="Email for API token auth")
    api_token: Optional[str] = Field(None, alias="apiToken", description="API token (will be encrypted)")
    project_filter: Optional[str] = Field(None, alias="projectFilter", description="Comma-separated project keys")

    class Config:
        populate_by_name = True


class InstanceCreate(InstanceBase):
    """Model for creating a new instance"""
    pass


class InstanceUpdate(BaseModel):
    """Model for updating an instance"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[str] = None
    auth_method: Optional[str] = None
    email: Optional[str] = None
    api_token: Optional[str] = None
    project_filter: Optional[str] = None


class Instance(InstanceBase):
    """Model for instance response"""
    id: str
    tenant_id: str
    status: str = Field(..., description="Status: 'idle', 'syncing', 'error'")
    last_sync_at: Optional[datetime] = None
    watermark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    """Model for test connection request"""
    base_url: str = Field(..., alias="baseUrl")
    email: str
    api_token: str = Field(..., alias="apiToken")
    auth_method: Optional[str] = Field(None, alias="authMethod")
    name: Optional[str] = None
    project_filter: Optional[str] = Field(None, alias="projectFilter")

    class Config:
        populate_by_name = True


class TestConnectionResponse(BaseModel):
    """Model for test connection response"""
    success: bool
    message: str
    details: Optional[dict] = None


class BackfillRequest(BaseModel):
    """Model for backfill request"""
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    project_keys: Optional[List[str]] = Field(None, description="Specific projects to backfill")


class SyncStatus(BaseModel):
    """Model for sync status response"""
    instance_id: str
    status: str
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    current_step: Optional[str] = None
    total_issues: Optional[int] = None
    processed_issues: Optional[int] = None
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")


class PaginatedInstancesResponse(BaseModel):
    """Paginated response for instances"""
    data: List[Instance]
    pagination: PaginationMeta


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=PaginatedInstancesResponse)
async def list_instances(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by name or URL"),
    db: Session = Depends(get_db),
):
    """
    List all Jira instances with pagination

    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page
    - **status**: Filter by status (idle, syncing, error)
    - **search**: Search by name or URL
    """
    # Query database
    query = db.query(JiraInstance)

    # Apply search filter
    if search:
        search_lower = f"%{search.lower()}%"
        query = query.filter(JiraInstance.base_url.ilike(search_lower))

    # Apply status filter
    if status:
        if status == "idle":
            query = query.filter(JiraInstance.is_active == True, JiraInstance.sync_enabled == False)
        elif status == "syncing":
            query = query.filter(JiraInstance.is_active == True, JiraInstance.sync_enabled == True)
        elif status == "error":
            query = query.filter(JiraInstance.is_connected == False)

    # Get total count
    total = query.count()

    # Apply pagination
    instances = query.offset((page - 1) * page_size).limit(page_size).all()

    # Convert to response format
    data = []
    for inst in instances:
        data.append({
            "id": str(inst.id),
            "tenant_id": str(inst.tenant_id),
            "name": inst.base_url.split("//")[1].split(".")[0] if "//" in inst.base_url else "Unknown",
            "base_url": inst.base_url,
            "auth_method": inst.auth_type,
            "email": inst.auth_email or "",
            "api_token": "***encrypted***" if inst.encrypted_credentials else "",
            "project_filter": "",
            "status": "syncing" if inst.sync_enabled else "idle",
            "last_sync_at": inst.last_sync_at,
            "watermark": None,
            "created_at": inst.created_at,
            "updated_at": inst.updated_at,
        })

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
    }


@router.post("", response_model=Instance, status_code=201)
async def create_instance(instance: InstanceCreate, db: Session = Depends(get_db)):
    """
    Create a new Jira instance

    - **name**: Instance name
    - **base_url**: Jira base URL
    - **auth_method**: Authentication method (api_token or oauth)
    - **email**: Email for API token auth
    - **api_token**: API token (will be encrypted before storage)
    - **project_filter**: Optional comma-separated project keys
    """
    # Get or create default tenant
    tenant = db.query(Tenant).first()
    if not tenant:
        tenant = Tenant(
            id=uuid4(),
            name="Default Tenant",
            slug="default",
            is_active=True,
        )
        db.add(tenant)
        db.flush()

    # Create new instance
    new_instance = JiraInstance(
        id=uuid4(),
        tenant_id=tenant.id,
        base_url=instance.base_url,
        auth_type=instance.auth_method,
        auth_email=instance.email,
        encrypted_credentials=instance.api_token,  # TODO: Encrypt this
        is_active=True,
        is_connected=False,
        sync_enabled=False,
    )

    db.add(new_instance)
    db.commit()
    db.refresh(new_instance)

    # Return response
    return {
        "id": str(new_instance.id),
        "tenant_id": str(new_instance.tenant_id),
        "name": instance.name,
        "base_url": new_instance.base_url,
        "auth_method": new_instance.auth_type,
        "email": new_instance.auth_email,
        "api_token": "***encrypted***",
        "project_filter": instance.project_filter or "",
        "status": "idle",
        "last_sync_at": new_instance.last_sync_at,
        "watermark": None,
        "created_at": new_instance.created_at,
        "updated_at": new_instance.updated_at,
    }


@router.get("/{instance_id}", response_model=Instance)
async def get_instance(instance_id: str):
    """
    Get a specific Jira instance by ID
    
    - **instance_id**: Instance ID
    """
    # TODO: Implement database query
    # For now, return mock data
    if instance_id == "not_found":
        raise HTTPException(status_code=404, detail="Instance not found")
    
    return {
        "id": instance_id,
        "tenant_id": "tenant_1",
        "name": "Production Jira",
        "base_url": "https://company.atlassian.net",
        "auth_method": "api_token",
        "email": "admin@company.com",
        "api_token": "***encrypted***",
        "project_filter": "PROJ1,PROJ2",
        "status": "idle",
        "last_sync_at": datetime.now(),
        "watermark": "2024-01-01T00:00:00Z",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.put("/{instance_id}", response_model=Instance)
async def update_instance(instance_id: str, instance: InstanceUpdate):
    """
    Update a Jira instance
    
    - **instance_id**: Instance ID
    - **instance**: Fields to update
    """
    # TODO: Implement database update
    # TODO: Re-encrypt API token if changed
    
    # For now, return mock response
    return {
        "id": instance_id,
        "tenant_id": "tenant_1",
        "name": instance.name or "Production Jira",
        "base_url": instance.base_url or "https://company.atlassian.net",
        "auth_method": instance.auth_method or "api_token",
        "email": instance.email or "admin@company.com",
        "api_token": "***encrypted***",
        "project_filter": instance.project_filter,
        "status": "idle",
        "last_sync_at": datetime.now(),
        "watermark": "2024-01-01T00:00:00Z",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.delete("/{instance_id}", status_code=204)
async def delete_instance(instance_id: str):
    """
    Delete a Jira instance
    
    - **instance_id**: Instance ID
    """
    # TODO: Implement database delete
    # TODO: Clean up related data (sync history, watermarks, etc.)
    
    # For now, just return success
    return None


@router.post("/{instance_id}/test", response_model=TestConnectionResponse)
async def test_connection(instance_id: str):
    """
    Test connection to a Jira instance
    
    - **instance_id**: Instance ID
    """
    # TODO: Implement MCP jira:test_connection call
    # TODO: Decrypt API token
    # TODO: Test connection to Jira
    
    # For now, return mock response
    return {
        "success": True,
        "message": "Connection successful",
        "details": {
            "jira_version": "9.4.0",
            "projects_found": 5,
            "user": "admin@company.com",
        }
    }


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection_direct(request: TestConnectionRequest):
    """
    Test connection to Jira (without saving instance)

    - **base_url**: Jira base URL
    - **email**: Email for authentication
    - **api_token**: API token
    """
    import sys
    import os

    # Add project root to path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from clients.python.jira_cloud_adapter import JiraCloudAdapter

        # Create adapter with provided credentials
        adapter = JiraCloudAdapter(
            base_url=request.base_url,
            email=request.email,
            api_token=request.api_token,
        )

        # Test connection by getting current user
        user_info = adapter.get_myself()

        return {
            "success": True,
            "message": "Connection successful",
            "details": {
                "user": user_info.get("displayName", request.email),
                "account_id": user_info.get("accountId"),
                "email": user_info.get("emailAddress", request.email),
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "details": None
        }


@router.post("/{instance_id}/backfill", status_code=202)
async def start_backfill(instance_id: str, request: BackfillRequest):
    """
    Start backfill for a Jira instance
    
    - **instance_id**: Instance ID
    - **start_date**: Optional start date (YYYY-MM-DD)
    - **end_date**: Optional end date (YYYY-MM-DD)
    - **project_keys**: Optional specific projects to backfill
    """
    # TODO: Implement MCP jira:start_backfill call
    # TODO: Create background task
    # TODO: Update instance status to 'syncing'
    
    # For now, return success
    return {"message": "Backfill started", "instance_id": instance_id}


@router.post("/{instance_id}/resync", status_code=202)
async def start_resync(instance_id: str):
    """
    Start incremental resync for a Jira instance
    
    - **instance_id**: Instance ID
    """
    # TODO: Implement incremental sync
    # TODO: Use watermark to sync only new/updated issues
    
    # For now, return success
    return {"message": "Resync started", "instance_id": instance_id}


@router.get("/{instance_id}/status", response_model=SyncStatus)
async def get_sync_status(instance_id: str):
    """
    Get sync status for a Jira instance
    
    - **instance_id**: Instance ID
    """
    # TODO: Implement MCP jira:get_sync_status call
    # TODO: Get real-time progress from background task
    
    # For now, return mock data
    return {
        "instance_id": instance_id,
        "status": "syncing",
        "progress": 45.5,
        "current_step": "Fetching issues from PROJ1",
        "total_issues": 1000,
        "processed_issues": 455,
        "started_at": datetime.now(),
        "estimated_completion": datetime.now(),
    }

