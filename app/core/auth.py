import os
from typing import Dict, Optional
import jwt
import time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from app.core.supabase import supabase

logger = logging.getLogger(__name__)

# Security scheme for JWT token authentication
security = HTTPBearer()

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "top_secret_jwt_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60 * 60  # 24 hours in seconds

def create_access_token(data: Dict) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the JWT
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    expiry = int(time.time()) + JWT_EXPIRATION
    to_encode.update({"exp": expiry})
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

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
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
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
            # Could auto-create profile here if needed
        
        return user
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return user  # Return the decoded token data even if profile validation fails

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