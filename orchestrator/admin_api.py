"""
Admin API Router for Digital Spiral Orchestrator

Provides REST API endpoints for Admin UI to manage Jira instances.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Import JiraClient for connection testing
try:
    from src.infrastructure.external.jira.client import JiraClient, JiraAPIError, JiraAuthenticationError
    JIRA_CLIENT_AVAILABLE = True
except ImportError:
    JIRA_CLIENT_AVAILABLE = False

    class JiraAPIError(Exception):
        """Fallback Jira API error used when the real client is unavailable."""

    class JiraAuthenticationError(Exception):
        """Fallback Jira authentication error used when the real client is unavailable."""

    JiraClient = None  # type: ignore
    logger.warning("JiraClient not available - using mock responses")

router = APIRouter(prefix="/api", tags=["admin"])


# ============================================================================
# Request/Response Models
# ============================================================================

class JiraInstanceCreate(BaseModel):
    """Request model for creating a Jira instance"""
    name: str = Field(..., description="Display name for the instance")
    base_url: str = Field(..., alias="baseUrl", description="Jira base URL (e.g., https://company.atlassian.net)")
    email: str = Field(..., description="Jira user email")
    api_token: str = Field(..., alias="apiToken", description="Jira API token")
    auth_method: str = Field(default="api_token", alias="authMethod", description="Authentication method")
    project_filter: Optional[str] = Field(None, alias="projectFilter", description="Optional project filter")

    class Config:
        populate_by_name = True


class JiraInstanceUpdate(BaseModel):
    """Request model for updating a Jira instance"""
    name: Optional[str] = None
    base_url: Optional[str] = Field(None, alias="baseUrl")
    email: Optional[str] = None
    api_token: Optional[str] = Field(None, alias="apiToken")
    auth_method: Optional[str] = Field(None, alias="authMethod")
    is_active: Optional[bool] = Field(None, alias="isActive")
    project_filter: Optional[str] = Field(None, alias="projectFilter")

    class Config:
        populate_by_name = True


class JiraInstanceResponse(BaseModel):
    """Response model for a Jira instance"""
    id: str
    name: str
    base_url: str = Field(alias="baseUrl")
    email: str
    auth_method: str = Field(alias="authMethod")
    is_active: bool = Field(alias="isActive")
    sync_status: str = Field(alias="syncStatus")
    last_sync_at: Optional[str] = Field(None, alias="lastSyncAt")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    user_id: Optional[str] = Field(None, alias="userId")
    user_email: Optional[str] = Field(None, alias="userEmail")

    class Config:
        populate_by_name = True
        by_alias = True


class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    pageSize: int
    total: int
    totalPages: int

    class Config:
        populate_by_name = True
        by_alias = True


class JiraInstanceListResponse(BaseModel):
    """Response model for listing Jira instances"""
    data: List[JiraInstanceResponse]
    pagination: PaginationInfo


class TestConnectionRequest(BaseModel):
    """Request model for testing Jira connection"""
    base_url: str = Field(alias="baseUrl")
    email: str
    api_token: str = Field(alias="apiToken")

    class Config:
        populate_by_name = True


class TestConnectionResponse(BaseModel):
    """Response model for test connection"""
    success: bool
    message: Optional[str] = None
    user: Optional[dict] = None
    rate_limit: Optional[dict] = None


# ============================================================================
# Jira Instance Management Endpoints
# ============================================================================

@router.get("/instances", response_model=JiraInstanceListResponse)
async def list_instances(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or URL"),
    status: Optional[str] = Query(None, description="Filter by sync status"),
    auth_method: Optional[str] = Query(None, description="Filter by auth method"),
    x_user_email: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
):
    """
    List all Jira instances with pagination and filtering for the authenticated user.
    """
    logger.info(f"Listing instances for user: {x_user_email}, page={page}, page_size={page_size}")

    if not x_user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # TODO: Implement actual database query filtered by user_email
    # For now, return mock data for this user
    mock_instances = [
        {
            "id": "inst-1",
            "name": "Main Jira",
            "base_url": "https://company.atlassian.net",
            "email": "admin@company.com",
            "auth_method": "api_token",
            "is_active": True,
            "sync_status": "synced",
            "last_sync_at": "2025-10-04T10:00:00Z",
            "created_at": "2025-10-01T00:00:00Z",
            "updated_at": "2025-10-04T10:00:00Z",
            "user_id": x_user_id,
            "user_email": x_user_email,
        }
    ]

    total = len(mock_instances)
    total_pages = (total + page_size - 1) // page_size  # Ceiling division

    return {
        "data": mock_instances,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": total_pages,
        },
    }


@router.post("/instances", response_model=JiraInstanceResponse, status_code=201)
async def create_instance(
    payload: JiraInstanceCreate,
    x_user_email: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_name: Optional[str] = Header(None),
):
    """
    Create a new Jira instance.
    """
    logger.info(f"Creating instance: {payload.name} for user: {x_user_email}")

    if not x_user_email:
        raise HTTPException(status_code=401, detail="User not authenticated")

    # TODO: Implement actual database query to check for duplicates
    # For now, use in-memory mock data
    # Check if instance with same base_url already exists for this user
    # mock_existing_instances = get_user_instances(x_user_email)
    # if any(inst["base_url"] == payload.base_url for inst in mock_existing_instances):
    #     raise HTTPException(
    #         status_code=409,
    #         detail=f"Instance with URL {payload.base_url} already exists for this user"
    #     )

    # TODO: Implement actual database insert
    # For now, return mock response
    return {
        "id": "inst-new",
        "name": payload.name,
        "base_url": payload.base_url,
        "email": payload.email,
        "auth_method": payload.auth_method,
        "is_active": True,
        "sync_status": "pending",
        "last_sync_at": None,
        "created_at": "2025-10-04T12:00:00Z",
        "updated_at": "2025-10-04T12:00:00Z",
        "user_id": x_user_id,
        "user_email": x_user_email,
    }


@router.get("/instances/{instance_id}", response_model=JiraInstanceResponse)
async def get_instance(instance_id: str):
    """
    Get a specific Jira instance by ID.
    """
    logger.info(f"Getting instance: {instance_id}")
    
    # TODO: Implement actual database query
    # For now, return mock data
    return {
        "id": instance_id,
        "name": "Main Jira",
        "base_url": "https://company.atlassian.net",
        "email": "admin@company.com",
        "auth_method": "api_token",
        "is_active": True,
        "sync_status": "synced",
        "last_sync_at": "2025-10-04T10:00:00Z",
        "created_at": "2025-10-01T00:00:00Z",
        "updated_at": "2025-10-04T10:00:00Z",
    }


@router.put("/instances/{instance_id}", response_model=JiraInstanceResponse)
async def update_instance(instance_id: str, payload: JiraInstanceUpdate):
    """
    Update a Jira instance.
    """
    logger.info(f"Updating instance: {instance_id}")
    
    # TODO: Implement actual database update
    # For now, return mock response
    return {
        "id": instance_id,
        "name": payload.name or "Main Jira",
        "base_url": payload.base_url or "https://company.atlassian.net",
        "email": payload.email or "admin@company.com",
        "auth_method": payload.auth_method or "api_token",
        "is_active": payload.is_active if payload.is_active is not None else True,
        "sync_status": "synced",
        "last_sync_at": "2025-10-04T10:00:00Z",
        "created_at": "2025-10-01T00:00:00Z",
        "updated_at": "2025-10-04T12:00:00Z",
    }


@router.delete("/instances/{instance_id}", status_code=204)
async def delete_instance(instance_id: str):
    """
    Delete a Jira instance (soft delete).
    """
    logger.info(f"Deleting instance: {instance_id}")
    
    # TODO: Implement actual database soft delete
    return None


# ============================================================================
# Connection Testing Endpoints
# ============================================================================

@router.post("/instances/test-connection", response_model=TestConnectionResponse)
async def test_connection(payload: TestConnectionRequest):
    """
    Test connection to a Jira instance without saving it.
    """
    logger.info(f"Testing connection to: {payload.base_url}")

    try:
        if JIRA_CLIENT_AVAILABLE:
            # Use real JiraClient to test connection
            client = JiraClient(
                base_url=payload.base_url,
                email=payload.email,
                api_token=payload.api_token,
                timeout=10,
            )

            # Get current user info to verify credentials
            user_info = await client.get_myself()

            # Close the client
            await client.close()

            return {
                "success": True,
                "message": "Connection successful",
                "user": {
                    "accountId": user_info.get("accountId", ""),
                    "displayName": user_info.get("displayName", ""),
                    "emailAddress": user_info.get("emailAddress", payload.email),
                },
                "rate_limit": {
                    "limit": 1000,
                    "remaining": 950,
                    "reset": 3600,
                },
            }
        else:
            # Fallback to mock response
            return {
                "success": True,
                "message": "Connection successful (mock)",
                "user": {
                    "accountId": "test-user-123",
                    "displayName": "Test User",
                    "emailAddress": payload.email,
                },
                "rate_limit": {
                    "limit": 1000,
                    "remaining": 950,
                    "reset": 3600,
                },
            }
    except JiraAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return {
            "success": False,
            "message": f"Authentication failed: {e.message}",
        }
    except JiraAPIError as e:
        logger.error(f"Jira API error: {e}")
        return {
            "success": False,
            "message": f"Jira API error: {e.message}",
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": str(e),
        }


@router.post("/instances/{instance_id}/test-connection", response_model=TestConnectionResponse)
async def test_instance_connection(instance_id: str):
    """
    Test connection for an existing Jira instance.
    """
    logger.info(f"Testing connection for instance: {instance_id}")
    
    try:
        # TODO: Implement actual Jira connection test
        # For now, return mock success
        return {
            "success": True,
            "message": "Connection successful",
            "user": {
                "accountId": "test-user-123",
                "displayName": "Test User",
                "emailAddress": "admin@company.com",
            },
            "rate_limit": {
                "limit": 1000,
                "remaining": 950,
                "reset": 3600,
            },
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return {
            "success": False,
            "message": str(e),
        }


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for Admin API"""
    return {"status": "ok", "service": "admin-api"}
