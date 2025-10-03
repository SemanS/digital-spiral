"""
OAuth Router for Atlassian/Jira OAuth 2.0 flow

This module provides endpoints for OAuth 2.0 authentication with Atlassian/Jira.
"""

import os
import secrets
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
from urllib.parse import urlencode

router = APIRouter(prefix="/api/oauth", tags=["oauth"])

# OAuth configuration from environment
ATLASSIAN_CLIENT_ID = os.getenv("ATLASSIAN_CLIENT_ID")
ATLASSIAN_CLIENT_SECRET = os.getenv("ATLASSIAN_CLIENT_SECRET")
ATLASSIAN_REDIRECT_URI = os.getenv("ATLASSIAN_REDIRECT_URI", "http://localhost:8000/api/oauth/callback")
ATLASSIAN_SCOPES = os.getenv(
    "ATLASSIAN_SCOPES",
    "offline_access read:jira-user read:jira-work write:jira-work"
)

# OAuth URLs
ATLASSIAN_AUTH_URL = "https://auth.atlassian.com/authorize"
ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"
ATLASSIAN_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

# In-memory state storage (in production, use Redis or database)
oauth_states = {}


class OAuthStartResponse(BaseModel):
    """Response for OAuth start"""
    auth_url: str
    state: str


class OAuthCallbackResponse(BaseModel):
    """Response for OAuth callback"""
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    cloud_id: Optional[str] = None
    site_url: Optional[str] = None
    error: Optional[str] = None


@router.get("/start", response_model=OAuthStartResponse)
async def start_oauth():
    """
    Start OAuth 2.0 flow
    
    Returns authorization URL and state parameter
    """
    if not ATLASSIAN_CLIENT_ID:
        raise HTTPException(500, "OAuth not configured: ATLASSIAN_CLIENT_ID missing")
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state (in production, use Redis with expiration)
    oauth_states[state] = {"created_at": "now"}
    
    # Build authorization URL
    params = {
        "audience": "api.atlassian.com",
        "client_id": ATLASSIAN_CLIENT_ID,
        "scope": ATLASSIAN_SCOPES,
        "redirect_uri": ATLASSIAN_REDIRECT_URI,
        "state": state,
        "response_type": "code",
        "prompt": "consent",
    }
    
    auth_url = f"{ATLASSIAN_AUTH_URL}?{urlencode(params)}"
    
    return {
        "auth_url": auth_url,
        "state": state,
    }


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """
    OAuth 2.0 callback endpoint
    
    Handles the redirect from Atlassian after user authorization
    """
    # Check for errors
    if error:
        return RedirectResponse(
            url=f"http://localhost:3002/admin/instances/new?error={error}&error_description={error_description or ''}"
        )
    
    # Validate state
    if not state or state not in oauth_states:
        return RedirectResponse(
            url="http://localhost:3002/admin/instances/new?error=invalid_state"
        )
    
    # Remove used state
    oauth_states.pop(state, None)
    
    # Validate code
    if not code:
        return RedirectResponse(
            url="http://localhost:3002/admin/instances/new?error=no_code"
        )
    
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                ATLASSIAN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": ATLASSIAN_CLIENT_ID,
                    "client_secret": ATLASSIAN_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": ATLASSIAN_REDIRECT_URI,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    token_response.status_code,
                    f"Token exchange failed: {token_response.text}"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in")
            
            # Get accessible resources (Jira sites)
            resources_response = await client.get(
                ATLASSIAN_RESOURCES_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            
            if resources_response.status_code != 200:
                raise HTTPException(
                    resources_response.status_code,
                    f"Failed to get resources: {resources_response.text}"
                )
            
            resources = resources_response.json()
            
            # Get first resource (site)
            if not resources:
                return RedirectResponse(
                    url="http://localhost:3002/admin/instances/new?error=no_resources"
                )
            
            first_resource = resources[0]
            cloud_id = first_resource.get("id")
            site_url = first_resource.get("url")
            site_name = first_resource.get("name")
            
            # Redirect back to frontend with tokens
            # In production, store tokens securely and redirect with session ID
            params = urlencode({
                "success": "true",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "cloud_id": cloud_id,
                "site_url": site_url,
                "site_name": site_name,
            })
            
            return RedirectResponse(
                url=f"http://localhost:3002/admin/instances/new?{params}"
            )
            
    except Exception as e:
        return RedirectResponse(
            url=f"http://localhost:3002/admin/instances/new?error=exception&error_description={str(e)}"
        )


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh OAuth access token
    
    - **refresh_token**: Refresh token from OAuth flow
    """
    if not ATLASSIAN_CLIENT_ID or not ATLASSIAN_CLIENT_SECRET:
        raise HTTPException(500, "OAuth not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ATLASSIAN_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": ATLASSIAN_CLIENT_ID,
                    "client_secret": ATLASSIAN_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    response.status_code,
                    f"Token refresh failed: {response.text}"
                )
            
            return response.json()
            
    except Exception as e:
        raise HTTPException(500, f"Token refresh failed: {str(e)}")

