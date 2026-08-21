import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LENGTH = 8
MIN_PRIORITY = 1
MAX_PRIORITY = 5


def validate_email_format(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_REGEX.match(value):
        raise ValueError("Invalid email address")
    return value


def validate_password_strength(value: str) -> str:
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    return value


def validate_not_blank(value: str, field_name: str = "field") -> str:
    """Strip whitespace and reject blank strings."""
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be blank or whitespace-only")
    return stripped


def validate_priority(value: int) -> int:
    if value < MIN_PRIORITY or value > MAX_PRIORITY:
        raise ValueError(
            f"Priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}"
        )
    return value
