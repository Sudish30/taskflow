import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 72
MIN_PRIORITY = 1
MAX_PRIORITY = 5

HAS_LETTER = re.compile(r"[A-Za-z]")
HAS_DIGIT = re.compile(r"[0-9]")


def validate_email_format(value: str) -> str:
    """Validate and normalize an email address."""
    value = value.strip().lower()
    if not EMAIL_REGEX.match(value):
        raise ValueError("Invalid email address")
    return value


def validate_password_strength(value: str) -> str:
    """Validate password against strength requirements.

    Rules:
    - At least 8 characters
    - At most 72 characters
    - Must contain at least one letter and one digit
    """
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    if len(value) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
        )
    if not HAS_LETTER.search(value) or not HAS_DIGIT.search(value):
        raise ValueError(
            "Password must contain at least one letter and one digit"
        )
    return value


def validate_priority(value: int) -> int:
    """Validate that priority is within the allowed range."""
    if value < MIN_PRIORITY or value > MAX_PRIORITY:
        raise ValueError(
            f"Priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}"
        )
    return value
