def error_content(code: str, message: str) -> dict:
    """Return the standard error envelope used by every API error response."""
    return {"error": {"code": code, "message": message}}
