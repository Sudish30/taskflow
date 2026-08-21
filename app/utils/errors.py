"""Shared error response helper for the standardized error envelope."""

from fastapi.responses import JSONResponse


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """Return a JSONResponse with the standard error envelope.

    Shape: {"error": {"code": "...", "message": "..."}}

    Args:
        code: A short snake_case string identifying the error type
              (e.g. ``"not_found"``, ``"unauthorized"``, ``"validation_error"``).
        message: A human-readable description of the error.
        status_code: The HTTP status code for the response.

    Returns:
        A :class:`fastapi.responses.JSONResponse` with the standardized body.
    """
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )
