"""
Request, error, and performance logging middleware for AgriSense AI.

Features:
  - Injects a unique X-Request-ID header on every response
  - Logs method, path, status code, and processing time for every request
  - Logs content-type and content-length for uploads
  - Performance warning when request exceeds a configurable threshold
  - Captures and logs unhandled exceptions before re-raising
"""

import time
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Performance warning threshold (ms)
SLOW_REQUEST_THRESHOLD_MS = 3000

logger = logging.getLogger("agrisense")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that logs every request with timing and injects X-Request-ID.

    Log format (INFO):
        REQUEST  POST /diagnose | 200 | 312.5ms | content-type=multipart/form-data

    Performance warning (WARNING):
        SLOW REQUEST POST /diagnose took 3512ms (threshold: 3000ms)
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Generate a unique request ID for distributed tracing
        request_id = str(uuid.uuid4())[:8]   # Short 8-char prefix for readability

        start_time = time.perf_counter()

        # Log incoming request
        content_type = request.headers.get("content-type", "")
        content_length = request.headers.get("content-length", "unknown")

        logger.debug(
            "REQUEST  %s %s | id=%s | content-type=%s | content-length=%s",
            request.method,
            request.url.path,
            request_id,
            content_type.split(";")[0],    # strip multipart boundary noise
            content_length,
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "UNHANDLED EXCEPTION  %s %s | id=%s | %.1fms | %s: %s",
                request.method,
                request.url.path,
                request_id,
                elapsed,
                type(exc).__name__,
                exc,
            )
            raise

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status_code = response.status_code

        # Choose log level based on status code
        if status_code >= 500:
            log_fn = logger.error
        elif status_code >= 400:
            log_fn = logger.warning
        else:
            log_fn = logger.info

        log_fn(
            "RESPONSE %s %s | id=%s | %d | %.1fms",
            request.method,
            request.url.path,
            request_id,
            status_code,
            elapsed_ms,
        )

        # Performance warning for slow requests
        if elapsed_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "SLOW REQUEST %s %s | id=%s | %.1fms (threshold: %dms)",
                request.method,
                request.url.path,
                request_id,
                elapsed_ms,
                SLOW_REQUEST_THRESHOLD_MS,
            )

        # Inject request-ID and timing headers into the response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)

        return response
