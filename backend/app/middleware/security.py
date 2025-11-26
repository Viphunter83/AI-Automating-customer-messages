import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Add security headers and basic validation"""
    
    async def dispatch(self, request: Request, call_next):
        # Check for suspicious patterns
        if self._is_suspicious_request(request):
            logger.warning(f"Suspicious request from {request.client.host if request.client else 'unknown'}: {request.url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request"
            )
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Check for suspicious patterns"""
        path = request.url.path.lower()
        
        # Check for SQL injection patterns
        sql_patterns = ["union", "select", "drop", "insert", "delete"]
        if any(pattern in path for pattern in sql_patterns):
            return True
        
        # Check for path traversal
        if "../" in path or "..\\" in path:
            return True
        
        return False

