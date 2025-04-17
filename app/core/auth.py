import os
from typing import Dict, Optional
import jwt
import time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.core.supabase import supabase
from app.core.config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT token authentication
security = HTTPBearer()

def validate_jwt_settings():
    """Validate JWT configuration on startup."""
    if not settings.JWT_SECRET:
        raise ValueError("JWT_SECRET environment variable is required")
    if len(settings.JWT_SECRET) < 32:
        raise ValueError("JWT_SECRET must be at least 32 characters long")

def create_access_token(data: Dict) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the JWT
        
    Returns:
        JWT token string
    """
    validate_jwt_settings()
    
    to_encode = data.copy()
    expiry = int(time.time()) + settings.JWT_EXPIRATION_SECONDS
    to_encode.update({
        "exp": expiry,
        "iat": int(time.time()),  # Issued at
        "type": "access"  # Token type
    })
    
    return jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )

def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid
    """
    validate_jwt_settings()
    
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Validate token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Get the current user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials with the JWT token
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    token = credentials.credentials
    user = decode_token(token)
    
    # Validate that user exists in the database
    try:
        filters = {"user_id": user.get("sub")}
        profiles = await supabase.select("profiles", filters=filters)
        
        if not profiles:
            logger.warning(f"No profile found for user ID {user.get('sub')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User profile not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error validating user profile",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def verify_organization_access(user_id: str, organization_id: str) -> bool:
    """
    Verify that a user has access to an organization.
    
    Args:
        user_id: User ID
        organization_id: Organization ID
        
    Returns:
        True if user has access, False otherwise
    """
    try:
        filters = {"owner_id": user_id, "id": organization_id}
        orgs = await supabase.select("organizations", filters=filters)
        return len(orgs) > 0
    except Exception as e:
        logger.error(f"Error verifying organization access: {str(e)}")
        return False