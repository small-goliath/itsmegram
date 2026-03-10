"""
Queue API Router
Job status and queue management endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.queue_manager import queue_manager

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Get the status of a queued job

    Args:
        job_id: The job ID to check

    Returns:
        Job status including position, wait time, and result (if completed)

    Raises:
        HTTPException 404: If job not found
    """
    status = queue_manager.get_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status


@router.get("/status")
async def get_queue_status():
    """
    Get overall queue statistics

    Returns:
        Queue statistics including pending, processing, completed, failed counts
    """
    return queue_manager.get_queue_stats()
