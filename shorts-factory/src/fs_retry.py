"""Small retry helpers for transient filesystem errors.

Google Drive File Provider sometimes raises EDEADLK while a file is being
hydrated or synced. Retrying only those transient I/O failures keeps the
pipeline from dropping a scheduled slot without hiding real errors.
"""
from __future__ import annotations

import errno
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

TRANSIENT_ERRNOS = {
    getattr(errno, "EDEADLK", 11),
    getattr(errno, "EAGAIN", 35),
    getattr(errno, "EBUSY", 16),
}


def is_transient_io_error(exc: BaseException) -> bool:
    if not isinstance(exc, OSError):
        return False
    if exc.errno in TRANSIENT_ERRNOS:
        return True
    return "resource deadlock avoided" in str(exc).lower()


def retry_io(
    func: Callable[[], T],
    *,
    attempts: int = 5,
    delay_sec: float = 2.0,
    backoff: float = 1.6,
) -> T:
    """Retry a callable for transient filesystem errors only."""
    wait = delay_sec
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except OSError as exc:
            if not is_transient_io_error(exc) or attempt >= attempts:
                raise
            if wait > 0:
                time.sleep(wait)
            wait *= backoff
    raise RuntimeError("unreachable")
