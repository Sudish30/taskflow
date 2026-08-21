import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 72
MIN_PRIORITY = 1
MAX_PRIORITY = 5


def validate_email_format(value: str) -> str:
    """Validate and normalise an email address."""
    value = value.strip().lower()
    if not EMAIL_REGEX.match(value):
        raise ValueError("Invalid email address")
    return value


def validate_password_strength(value: str) -> str:
    """Enforce password complexity rules.

    Rules (checked in order):
    - At least ``MIN_PASSWORD_LENGTH`` characters.
    - At most ``MAX_PASSWORD_LENGTH`` characters.
    - Contains at least one letter (A-Z or a-z).
    - Contains at least one digit (0-9).

    Returns the original value unchanged when all rules pass.
    Raises ``ValueError`` with a message that identifies the failing rule.
    """
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    if len(value) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
        )
    if not re.search(r"[A-Za-z]", value):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit")
    return value


def validate_priority(value: int) -> int:
    """Validate that a priority value falls within the allowed range."""
    if value < MIN_PRIORITY or value > MAX_PRIORITY:
        raise ValueError(
            f"Priority must be between {MIN_PRIORITY} and {MAX_PRIORITY}"
        )
    return value
