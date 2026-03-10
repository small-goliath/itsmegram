"""
Metrics Collection Service
Collects and aggregates key metrics for monitoring
"""

import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger()


@dataclass
class MetricsCollector:
    """
    Simple in-memory metrics collector
    - Tracks processing times, error counts, cache hit/miss
    - Maintains rolling window of recent data
    """

    # Processing times (last 1000)
    processing_times: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Error counts by type
    error_counts: Dict[str, int] = field(default_factory=dict)

    # Cache hits/misses
    cache_hits: int = 0
    cache_misses: int = 0

    # Request counts
    total_requests: int = 0
    successful_requests: int = 0

    # Instagram specific metrics
    instagram_requests: int = 0
    instagram_failures: int = 0
    rate_limit_hits: int = 0

    # Timestamps for rate calculation
    _start_time: datetime = field(default_factory=datetime.utcnow)

    def record_processing_time(self, duration: float) -> None:
        """Record a processing time"""
        self.processing_times.append(duration)

    def record_error(self, error_type: str) -> None:
        """Record an error occurrence"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    def record_cache_hit(self) -> None:
        """Record a cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss"""
        self.cache_misses += 1

    def record_request(self, success: bool) -> None:
        """Record a request"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1

    def record_instagram_request(self, success: bool) -> None:
        """Record an Instagram API request"""
        self.instagram_requests += 1
        if not success:
            self.instagram_failures += 1

    def record_rate_limit_hit(self) -> None:
        """Record a rate limit hit"""
        self.rate_limit_hits += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics"""
        # Calculate average processing time
        avg_time = 0.0
        if self.processing_times:
            avg_time = sum(self.processing_times) / len(self.processing_times)

        # Calculate cache hit ratio
        total_cache = self.cache_hits + self.cache_misses
        cache_hit_ratio = self.cache_hits / total_cache if total_cache > 0 else 0

        # Calculate success rate
        success_rate = (
            self.successful_requests / self.total_requests
            if self.total_requests > 0 else 0
        )

        # Calculate Instagram success rate
        instagram_success_rate = (
            (self.instagram_requests - self.instagram_failures) / self.instagram_requests
            if self.instagram_requests > 0 else 0
        )

        # Calculate uptime
        uptime = datetime.utcnow() - self._start_time

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(uptime.total_seconds()),
            "processing": {
                "avg_processing_time": round(avg_time, 3),
                "total_processed": len(self.processing_times),
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_ratio": round(cache_hit_ratio, 3),
            },
            "requests": {
                "total": self.total_requests,
                "successful": self.successful_requests,
                "success_rate": round(success_rate, 3),
            },
            "instagram": {
                "requests": self.instagram_requests,
                "failures": self.instagram_failures,
                "success_rate": round(instagram_success_rate, 3),
                "rate_limit_hits": self.rate_limit_hits,
            },
            "errors": self.error_counts,
        }

    def reset(self) -> None:
        """Reset all metrics"""
        self.processing_times.clear()
        self.error_counts.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.instagram_requests = 0
        self.instagram_failures = 0
        self.rate_limit_hits = 0
        self._start_time = datetime.utcnow()
        logger.info("metrics_reset")


# Singleton instance
metrics = MetricsCollector()
