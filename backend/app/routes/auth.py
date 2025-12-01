"""
Authentication Routes
Login and token management for operators
"""
import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_operator
from app.auth.jwt import create_access_token, verify_password
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model"""
    operator_id: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    operator_id: str
    expires_in: int  # seconds


class TokenResponse(BaseModel):
    """Token validation response"""
    valid: bool
    operator_id: Optional[str] = None


# In-memory operator credentials (in production, use database)
# Format: {operator_id: hashed_password}
OPERATOR_CREDENTIALS = {
    # Default operators for testing
    # Password for all: "operator123" (bcrypt hash)
    "operator_001": "$2b$12$BnRjcI4iR8a0m7qH8O8coedXrYIAnL9Gh6fhGNDcXW6k/iKyhP/gC",  # operator123
    "operator_002": "$2b$12$WJs0mYvAusSGQm.igexxC.DZgRGrQXPA6JFG6ldMrsvV4RkObj0ue",  # operator123
}


def authenticate_operator(operator_id: str, password: str) -> bool:
    """
    Authenticate operator credentials
    
    In production, this should query a database.
    For now, we use in-memory credentials.
    
    Args:
        operator_id: Operator ID
        password: Plain text password
    
    Returns:
        True if credentials are valid, False otherwise
    """
    hashed_password = OPERATOR_CREDENTIALS.get(operator_id)
    if not hashed_password:
        return False
    
    return verify_password(password, hashed_password)


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    Login endpoint for operators
    
    Returns JWT access token for authenticated operators.
    
    Rate limiting: Global rate limiting applies (60/minute per IP via slowapi middleware).
    For production, consider adding stricter rate limiting for login endpoint.
    
    Example:
        POST /api/auth/login
        {
            "operator_id": "operator_001",
            "password": "operator123"
        }
    """
    # Authenticate operator
    if not authenticate_operator(login_data.operator_id, login_data.password):
        logger.warning(f"Failed login attempt for operator: {login_data.operator_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect operator ID or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=60 * 24)  # 24 hours
    access_token = create_access_token(
        data={"sub": login_data.operator_id},
        expires_delta=access_token_expires,
    )
    
    logger.info(f"✅ Operator {login_data.operator_id} logged in successfully")
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        operator_id=login_data.operator_id,
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.get("/me", response_model=TokenResponse)
async def get_current_operator_info(
    operator_id: str = Depends(get_current_operator),
):
    """
    Get current authenticated operator information
    
    Requires valid JWT token in Authorization header.
    """
    return TokenResponse(valid=True, operator_id=operator_id)


class TokenValidateRequest(BaseModel):
    """Token validation request model"""
    token: str = Field(..., min_length=1)


@router.post("/validate", response_model=TokenResponse)
async def validate_token(request_data: TokenValidateRequest):
    """
    Validate a JWT token
    
    Token should be passed in request body, not URL parameter (for security).
    
    Args:
        request_data: Token validation request with token in body
    
    Returns:
        Token validation result
    """
    from app.auth.jwt import get_user_id_from_token
    
    operator_id = get_user_id_from_token(request_data.token)
    if operator_id:
        return TokenResponse(valid=True, operator_id=operator_id)
    return TokenResponse(valid=False)

