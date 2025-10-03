"""JWT authentication for Digital Spiral."""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


class TokenData(BaseModel):
    """JWT token data."""

    user_id: str
    tenant_id: UUID
    email: str
    roles: list[str] = []
    exp: datetime


class JWTAuth:
    """JWT authentication service."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        """Initialize JWT auth.

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.security = HTTPBearer()

    def create_access_token(
        self,
        user_id: str,
        tenant_id: UUID,
        email: str,
        roles: list[str] = None,
    ) -> str:
        """Create access token.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            email: User email
            roles: User roles

        Returns:
            JWT access token
        """
        expires = datetime.now(timezone.utc) + timedelta(
            minutes=self.access_token_expire_minutes
        )
        
        payload = {
            "user_id": user_id,
            "tenant_id": str(tenant_id),
            "email": email,
            "roles": roles or [],
            "exp": expires,
            "type": "access",
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: UUID,
    ) -> str:
        """Create refresh token.

        Args:
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            JWT refresh token
        """
        expires = datetime.now(timezone.utc) + timedelta(
            days=self.refresh_token_expire_days
        )
        
        payload = {
            "user_id": user_id,
            "tenant_id": str(tenant_id),
            "exp": expires,
            "type": "refresh",
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token.

        Args:
            token: JWT token

        Returns:
            Token data

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            
            return TokenData(
                user_id=payload["user_id"],
                tenant_id=UUID(payload["tenant_id"]),
                email=payload["email"],
                roles=payload.get("roles", []),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            )
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify refresh token.

        Args:
            token: JWT refresh token

        Returns:
            Token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            
            # Check token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    ) -> TokenData:
        """Get current user from JWT token.

        Args:
            credentials: HTTP authorization credentials

        Returns:
            Token data

        Raises:
            HTTPException: If token is invalid
        """
        token = credentials.credentials
        return self.verify_token(token)

    def require_role(self, required_role: str):
        """Require specific role.

        Args:
            required_role: Required role

        Returns:
            Dependency function
        """
        async def role_checker(
            token_data: TokenData = Depends(self.get_current_user),
        ) -> TokenData:
            if required_role not in token_data.roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required",
                )
            return token_data
        
        return role_checker

    def require_any_role(self, required_roles: list[str]):
        """Require any of the specified roles.

        Args:
            required_roles: List of required roles

        Returns:
            Dependency function
        """
        async def role_checker(
            token_data: TokenData = Depends(self.get_current_user),
        ) -> TokenData:
            if not any(role in token_data.roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of roles {required_roles} required",
                )
            return token_data
        
        return role_checker


# Global JWT auth instance
_jwt_auth: Optional[JWTAuth] = None


def get_jwt_auth() -> JWTAuth:
    """Get global JWT auth instance.

    Returns:
        JWTAuth instance
    """
    global _jwt_auth
    if _jwt_auth is None:
        _jwt_auth = JWTAuth()
    return _jwt_auth


# Convenience dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> TokenData:
    """Get current user from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        Token data
    """
    auth = get_jwt_auth()
    return auth.verify_token(credentials.credentials)


def require_admin():
    """Require admin role."""
    return get_jwt_auth().require_role("admin")


def require_user():
    """Require user or admin role."""
    return get_jwt_auth().require_any_role(["user", "admin"])


__all__ = [
    "TokenData",
    "JWTAuth",
    "get_jwt_auth",
    "get_current_user",
    "require_admin",
    "require_user",
]

