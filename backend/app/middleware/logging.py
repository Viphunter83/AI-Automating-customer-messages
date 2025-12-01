import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Add request/response logging with correlation IDs"""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"[{request_id}] Exception: {type(e).__name__}: {str(e)}", exc_info=True
            )
            raise
        finally:
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"[{request_id}] {response.status_code} " f"duration={duration:.3f}s"
            )

        response.headers["X-Request-ID"] = request_id
        return response
