"""
Circuit Breaker Pattern Implementation
Prevents cascading failures when Instagram blocks requests
"""

import asyncio
import time
from enum import Enum
from typing import Optional, Callable, Any

import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing state


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""

    pass


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation
    - Blocks requests after consecutive failures
    - Auto-recovery after timeout
    """

    def __init__(
        self,
        failure_threshold: int = 10,
        recovery_timeout: float = 300,  # 5 minutes
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    logger.info("circuit_breaker_half_open")
                else:
                    raise CircuitBreakerOpenError(
                        "Service temporarily unavailable. Please try again later."
                    )

            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        "Circuit breaker half-open limit reached"
                    )
                self.half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e

    async def _on_success(self) -> None:
        async with self._lock:
            self.failure_count = 0

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    self.half_open_calls = 0
                    logger.info("circuit_breaker_closed")

    async def _on_failure(self) -> None:
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_opened",
                    failures=self.failure_count,
                    threshold=self.failure_threshold,
                )

    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        time_since_failure = None
        if self.last_failure_time:
            time_since_failure = round(time.time() - self.last_failure_time, 2)

        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "time_since_failure": time_since_failure,
            "recovery_timeout": self.recovery_timeout,
        }

    def reset(self) -> None:
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
        logger.info("circuit_breaker_reset")


# Singleton instance for Instagram service
instagram_circuit_breaker = CircuitBreaker(
    failure_threshold=5,  # Open after 5 failures
    recovery_timeout=300,  # Try recovery after 5 minutes
    half_open_max_calls=2,
)
