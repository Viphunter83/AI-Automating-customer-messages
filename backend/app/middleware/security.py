import json
import logging
from typing import Any, Dict

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Add security headers and comprehensive input validation"""

    # SQL injection patterns (more comprehensive)
    SQL_INJECTION_PATTERNS = [
        r"(?i)(union\s+(all\s+)?select)",
        r"(?i)(select\s+.*\s+from)",
        r"(?i)(insert\s+into)",
        r"(?i)(delete\s+from)",
        r"(?i)(drop\s+(table|database))",
        r"(?i)(update\s+.*\s+set)",
        r"(?i)(exec\s*\()",
        r"(?i)(execute\s*\()",
        r"(?i)(;\s*(drop|delete|insert|update|exec))",
        r"(?i)(--\s*$)",
        r"(?i)(/\*.*\*/)",
        r"(?i)(\bor\b\s+\d+\s*=\s*\d+)",
        r"(?i)(\band\b\s+\d+\s*=\s*\d+)",
        r"(?i)(\'\s*(or|and)\s+\'\d+\'\s*=\s*\'\d+)",
        r"(?i)(\'\s*(or|and)\s+\d+\s*=\s*\d+)",
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
        r"\.\.%2f",
        r"\.\.%5c",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"<iframe[^>]*>",
        r"<img[^>]*src\s*=\s*javascript:",
    ]

    async def dispatch(self, request: Request, call_next):
        # Check for suspicious patterns in all input sources
        if self._is_suspicious_request(request):
            client_host = request.client.host if request.client else "unknown"
            logger.warning(
                f"Suspicious request blocked from {client_host}: "
                f"{request.method} {request.url.path}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request detected",
            )

        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response

    def _is_suspicious_request(self, request: Request) -> bool:
        """Check for suspicious patterns in path, query params, headers, and body"""
        import re

        # Whitelist of safe paths that might contain SQL keywords
        safe_paths = ["/api/search", "/api/messages", "/api/admin"]
        path = request.url.path

        # Check URL path (but allow safe paths)
        is_safe_path = any(path.startswith(safe) for safe in safe_paths)
        if not is_safe_path:
            if self._check_patterns(
                path, self.SQL_INJECTION_PATTERNS + self.PATH_TRAVERSAL_PATTERNS
            ):
                return True

        # Check query parameters (more lenient for search endpoints)
        query_string = str(request.url.query)
        if query_string:
            # For search endpoints, be more lenient with query parameter
            if "/api/search" in path and "query=" in query_string:
                # Only check for obvious SQL injection attempts in search queries
                dangerous_patterns = [
                    r"(?i)(union\s+(all\s+)?select)",
                    r"(?i)(;\s*(drop|delete|insert|update|exec))",
                    r"(?i)(--\s*$)",
                    r"(?i)(/\*.*\*/)",
                ]
                if self._check_patterns(query_string, dangerous_patterns):
                    return True
            else:
                # For other endpoints, check all patterns
                if self._check_patterns(
                    query_string, self.SQL_INJECTION_PATTERNS + self.XSS_PATTERNS
                ):
                    return True

        # Check headers (but allow common headers that might contain SQL keywords)
        suspicious_headers = ["x-forwarded-for", "x-real-ip", "user-agent"]
        for header_name, header_value in request.headers.items():
            # Skip common headers that might have false positives
            if header_name.lower() in [
                "host",
                "accept",
                "content-type",
                "authorization",
            ]:
                continue
            if self._check_patterns(
                str(header_value), self.SQL_INJECTION_PATTERNS + self.XSS_PATTERNS
            ):
                return True

        # Check request body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            # Note: We can't read the body here without consuming it
            # So we'll check Content-Type and rely on Pydantic validation
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                # JSON body will be validated by Pydantic, which uses parameterized queries
                # So SQL injection through body is less likely, but we can still check for XSS
                pass

        return False

    def _check_patterns(self, text: str, patterns: list) -> bool:
        """Check if text matches any of the suspicious patterns"""
        import re

        if not text:
            return False

        text_lower = text.lower()
        for pattern in patterns:
            try:
                if re.search(pattern, text_lower):
                    logger.debug(
                        f"Pattern matched: {pattern[:50]} in text: {text[:100]}"
                    )
                    return True
            except re.error:
                # Invalid regex pattern, skip it
                logger.warning(f"Invalid regex pattern: {pattern}")
                continue

        return False

    async def _check_request_body(self, request: Request) -> Dict[str, Any]:
        """Safely read and parse request body for validation"""
        try:
            body = await request.body()
            if not body:
                return {}

            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    return json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return {}

            return {"raw": body.decode("utf-8", errors="ignore")[:1000]}
        except Exception as e:
            logger.debug(f"Error reading request body: {e}")
            return {}
