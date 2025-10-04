"""API dependencies."""

from typing import Optional
from uuid import UUID

from fastapi import Header, HTTPException


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    """Get current user from authorization header.
    
    Args:
        authorization: Authorization header
        
    Returns:
        User information
        
    Raises:
        HTTPException: If unauthorized
    """
    # TODO: Implement actual authentication
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Mock user for now
    return {
        "id": "user-123",
        "email": "user@example.com",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
    }


async def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None),
    current_user: dict = None,
) -> UUID:
    """Get tenant ID from header or current user.
    
    Args:
        x_tenant_id: Tenant ID header
        current_user: Current user
        
    Returns:
        Tenant ID
        
    Raises:
        HTTPException: If tenant ID not found
    """
    # Try header first
    if x_tenant_id:
        try:
            return UUID(x_tenant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant ID")
    
    # Fall back to user's tenant
    if current_user and "tenant_id" in current_user:
        return UUID(current_user["tenant_id"])
    
    # Default test tenant
    return UUID("00000000-0000-0000-0000-000000000001")

