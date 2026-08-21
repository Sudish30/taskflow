"""Request logging middleware for TaskFlow.

Logs one line per request: method, path, response status, and duration in
milliseconds.  The ``/health`` path is excluded so liveness probes don't
flood the log.  Request bodies and Authorization headers are never logged.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("taskflow.requests")

EXCLUDED_PATHS = {"/health"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that emits a single INFO log line for every non-excluded request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request, log it (unless excluded), and return the response."""
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start_time) * 1000

        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
