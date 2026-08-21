"""Module-level singleton for the login rate limiter.

Import ``login_rate_limiter`` from here to share the same instance across
all requests in a single-process deployment.  To swap the backend (e.g. to
a Redis-backed implementation), change only this file.
"""

from app.utils.rate_limiter import InMemoryLoginRateLimiter

login_rate_limiter = InMemoryLoginRateLimiter(max_attempts=5, window_seconds=60)
