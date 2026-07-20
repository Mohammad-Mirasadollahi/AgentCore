"""Simple sliding-window RPM limiter for the LiteLLM gateway."""

from __future__ import annotations

import threading
import time


class RpmLimiter:
    """Allow at most `rpm` acquisitions per rolling 60-second window."""

    def __init__(self, rpm: int) -> None:
        if rpm < 1:
            raise ValueError("rpm must be >= 1")
        self.rpm = rpm
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> float:
        """Block until a slot is available. Returns seconds waited (0 if immediate)."""
        waited = 0.0
        while True:
            with self._lock:
                now = time.monotonic()
                cutoff = now - 60.0
                self._timestamps = [t for t in self._timestamps if t > cutoff]
                if len(self._timestamps) < self.rpm:
                    self._timestamps.append(now)
                    return waited
                sleep_for = max(0.01, 60.0 - (now - self._timestamps[0]))
            time.sleep(sleep_for)
            waited += sleep_for
