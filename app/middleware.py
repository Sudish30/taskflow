"""Request logging middleware for TaskFlow."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("taskflow.requests")

EXCLUDED_PATHS = {"/health"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs one line per request: method, path, status code, and duration.

    Excludes paths listed in ``EXCLUDED_PATHS`` (e.g. ``/health``) so that
    liveness/readiness probes don't flood the log.  Only ``request.method``,
    ``request.url.path``, the response status code, and elapsed time are
    logged — request bodies and headers (including ``Authorization``) are
    never touched.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and emit a log record (unless path is excluded)."""
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
