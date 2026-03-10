"""
Metrics API Router
Exposes system metrics for monitoring
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.services.metrics_service import metrics
from app.services.queue_manager import queue_manager
from app.services.rate_limiter import instagram_rate_limiter
from app.services.circuit_breaker import instagram_circuit_breaker

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
async def get_all_metrics() -> Dict[str, Any]:
    """
    Get all system metrics
    Includes processing times, cache stats, queue stats, rate limiter status
    """
    return {
        "metrics": metrics.get_metrics(),
        "queue": queue_manager.get_queue_stats(),
        "rate_limiter": instagram_rate_limiter.get_status(),
        "circuit_breaker": instagram_circuit_breaker.get_status(),
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Simple health check with basic metrics
    """
    metrics_data = metrics.get_metrics()

    # Determine health status
    is_healthy = True
    issues = []

    # Check success rate
    if metrics_data["requests"]["success_rate"] < 0.8 and metrics_data["requests"]["total"] > 10:
        is_healthy = False
        issues.append("Low request success rate")

    # Check Instagram success rate
    if metrics_data["instagram"]["success_rate"] < 0.5 and metrics_data["instagram"]["requests"] > 5:
        is_healthy = False
        issues.append("Instagram API experiencing high failure rate")

    # Check circuit breaker
    cb_status = instagram_circuit_breaker.get_status()
    if cb_status["state"] == "open":
        is_healthy = False
        issues.append("Circuit breaker is open")

    return {
        "healthy": is_healthy,
        "issues": issues,
        "timestamp": metrics_data["timestamp"],
        "summary": {
            "total_requests": metrics_data["requests"]["total"],
            "success_rate": metrics_data["requests"]["success_rate"],
            "instagram_requests": metrics_data["instagram"]["requests"],
            "instagram_success_rate": metrics_data["instagram"]["success_rate"],
            "circuit_breaker_state": cb_status["state"],
        },
    }


@router.post("/reset")
async def reset_metrics() -> Dict[str, str]:
    """
    Reset all metrics (admin only)
    """
    metrics.reset()
    return {"status": "metrics reset"}
