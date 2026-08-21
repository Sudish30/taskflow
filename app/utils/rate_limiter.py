"""Rate limiter abstractions and in-memory implementation for login attempts."""

import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple


class LoginRateLimiter(ABC):
    """Abstract base class for login rate limiters."""

    @abstractmethod
    def record_failure(self, key: str) -> None:
        """Record a failed login attempt for the given key."""
        ...

    @abstractmethod
    def record_success(self, key: str) -> None:
        """Reset the failure counter for the given key after a successful login."""
        ...

    @abstractmethod
    def is_blocked(self, key: str) -> Tuple[bool, int]:
        """Check whether the key is currently rate-limited.

        Returns:
            A tuple of (blocked: bool, retry_after_seconds: int).
            retry_after_seconds is 0 when not blocked.
        """
        ...


class InMemoryLoginRateLimiter(LoginRateLimiter):
    """In-memory implementation of LoginRateLimiter using a sliding window.

    Tracks failure timestamps per key in a dict protected by a threading.Lock.
    Suitable for single-process deployments; swap out for a Redis-backed
    implementation by subclassing LoginRateLimiter.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60) -> None:
        """Initialise the limiter.

        Args:
            max_attempts: Number of failures allowed before the key is blocked.
            window_seconds: Sliding window duration in seconds.
        """
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._store: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prune(self, key: str, now: float) -> list[float]:
        """Remove timestamps outside the current window and return the remainder.

        Must be called while holding ``self._lock``.
        """
        timestamps = self._store.get(key, [])
        fresh = [ts for ts in timestamps if now - ts < self._window_seconds]
        if fresh:
            self._store[key] = fresh
        else:
            self._store.pop(key, None)
        return fresh

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_failure(self, key: str) -> None:
        """Append the current timestamp to the key's failure list."""
        now = time.time()
        with self._lock:
            timestamps = self._store.get(key, [])
            timestamps.append(now)
            # Prune stale entries after appending so the list stays compact.
            fresh = [ts for ts in timestamps if now - ts < self._window_seconds]
            self._store[key] = fresh

    def record_success(self, key: str) -> None:
        """Clear the failure record for the key after a successful login."""
        with self._lock:
            self._store.pop(key, None)

    def is_blocked(self, key: str) -> Tuple[bool, int]:
        """Return (blocked, retry_after_seconds) for the given key."""
        now = time.time()
        with self._lock:
            fresh = self._prune(key, now)
            if len(fresh) >= self._max_attempts:
                oldest = fresh[0]
                retry_after = int(self._window_seconds - (now - oldest)) + 1
                retry_after = max(1, retry_after)
                return True, retry_after
            return False, 0

    def reset(self, key: Optional[str] = None) -> None:
        """Reset rate-limit state.

        Args:
            key: If provided, clears only that key's record.
                 If ``None``, clears all records.
        """
        with self._lock:
            if key is None:
                self._store.clear()
            else:
                self._store.pop(key, None)
