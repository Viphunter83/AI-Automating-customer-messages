"""
Authentication Dependencies for FastAPI
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_token, get_user_id_from_token

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_operator(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Get current authenticated operator ID from JWT token
    
    Usage:
        @router.get("/protected")
        async def protected_route(operator_id: str = Depends(get_current_operator)):
            return {"operator_id": operator_id}
    
    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract operator ID (subject)
    operator_id = payload.get("sub")
    if not operator_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing operator ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return operator_id


async def get_optional_operator(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[str]:
    """
    Get current operator ID if authenticated, None otherwise
    
    Usage:
        @router.get("/optional")
        async def optional_route(operator_id: Optional[str] = Depends(get_optional_operator)):
            if operator_id:
                return {"operator_id": operator_id}
            return {"message": "Not authenticated"}
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        operator_id = get_user_id_from_token(token)
        return operator_id
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None










