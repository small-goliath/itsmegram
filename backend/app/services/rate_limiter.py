"""
Adaptive Rate Limiter for Instagram requests
Token bucket with dynamic adjustment based on success/failure rates
"""

import asyncio
import random
import time
from typing import Optional

import structlog

logger = structlog.get_logger()


class AdaptiveRateLimiter:
    """
    Adaptive Token Bucket Rate Limiter
    - Dynamically adjusts rate based on Instagram response
    - Adds jitter to avoid bot detection patterns
    """

    def __init__(
        self,
        tokens_per_second: float = 5.0,
        bucket_size: int = 10,
        jitter_range: tuple = (0.1, 0.3),
    ):
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.jitter_range = jitter_range

        self.tokens: float = bucket_size
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

        # Statistics for adaptive adjustment
        self.consecutive_successes = 0
        self.consecutive_failures = 0

    async def acquire(self) -> None:
        """Acquire a token (wait if none available)"""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Replenish tokens based on elapsed time
            self.tokens = min(
                self.bucket_size,
                self.tokens + elapsed * self.tokens_per_second,
            )
            self.last_update = now

            if self.tokens < 1:
                # Not enough tokens: calculate wait time
                wait_time = (1 - self.tokens) / self.tokens_per_second
                jitter = random.uniform(*self.jitter_range)
                total_wait = wait_time + jitter

                logger.debug("rate_limiter_waiting", wait_time=total_wait)

                # Release lock while waiting
                self.lock.release()
                try:
                    await asyncio.sleep(total_wait)
                finally:
                    await self.lock.acquire()

                # Recalculate tokens after wait
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(
                    self.bucket_size,
                    self.tokens + elapsed * self.tokens_per_second,
                )
                self.last_update = now

            self.tokens -= 1

    def report_success(self) -> None:
        """Call on successful request - gradually increase rate"""
        self.consecutive_successes += 1
        self.consecutive_failures = 0

        # After 10 consecutive successes, increase rate slightly
        if self.consecutive_successes >= 10:
            self.tokens_per_second = min(10.0, self.tokens_per_second + 0.5)
            self.bucket_size = min(20, self.bucket_size + 1)
            logger.info(
                "rate_limiter_increased",
                tokens_per_second=self.tokens_per_second,
                bucket_size=self.bucket_size,
            )
            self.consecutive_successes = 0

    def report_rate_limited(self) -> None:
        """Call on 429 response - decrease rate significantly"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0

        # Decrease rate on rate limit
        self.tokens_per_second = max(1.0, self.tokens_per_second - 1.0)
        self.bucket_size = max(5, self.bucket_size - 2)

        logger.warning(
            "rate_limiter_decreased",
            tokens_per_second=self.tokens_per_second,
            bucket_size=self.bucket_size,
            consecutive_failures=self.consecutive_failures,
        )

    def get_status(self) -> dict:
        """Return current rate limiter status"""
        return {
            "tokens_per_second": round(self.tokens_per_second, 2),
            "bucket_size": self.bucket_size,
            "available_tokens": round(self.tokens, 2),
            "consecutive_successes": self.consecutive_successes,
            "consecutive_failures": self.consecutive_failures,
        }


# Singleton instance for global Instagram request limiting
instagram_rate_limiter = AdaptiveRateLimiter()
