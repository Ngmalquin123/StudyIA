"""Límite de intentos fallidos de login, en memoria.

Basta para un solo proceso (desarrollo / MVP). Si la API se despliega con varios
workers, cada uno lleva su propia cuenta: habría que mover esto a Redis.
"""
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from studyia.core.config import settings


class LoginRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        failures = self._failures[key]
        while failures and now - failures[0] > self.window_seconds:
            failures.popleft()
        return failures

    def retry_after(self, key: str) -> int:
        """Segundos que faltan para poder reintentar; 0 si no está bloqueado."""
        with self._lock:
            now = monotonic()
            failures = self._prune(key, now)
            if len(failures) < self.max_attempts:
                return 0
            return int(self.window_seconds - (now - failures[0])) + 1

    def register_failure(self, key: str) -> None:
        with self._lock:
            self._failures[key].append(monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


login_rate_limiter = LoginRateLimiter(
    max_attempts=settings.login_max_attempts,
    window_seconds=settings.login_lockout_minutes * 60,
)
