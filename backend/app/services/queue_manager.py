"""
Queue Manager for request queuing and sequential processing
Uses asyncio.Queue for async task management
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable

import structlog

logger = structlog.get_logger()


class QueueStatus(str, Enum):
    """Queue job status enum"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class QueueManager:
    """
    In-memory request queue manager
    - Uses asyncio.Queue
    - Max 100 queue size limit
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        max_queue_size: int = 100,
        requests_per_second: float = 5.0,
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.requests_per_second = requests_per_second

        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.processing = False

    async def start(self) -> None:
        """Start the queue processor"""
        if not self.processing:
            self.processing = True
            asyncio.create_task(self._process_queue())
            logger.info("queue_manager_started")

    async def stop(self) -> None:
        """Stop the queue processor"""
        self.processing = False
        logger.info("queue_manager_stopped")

    async def enqueue(
        self,
        username: str,
        task_func: Callable,
        *args,
        **kwargs,
    ) -> Optional[str]:
        """
        Add a task to the queue

        Args:
            username: Instagram username being analyzed
            task_func: Async function to execute
            *args, **kwargs: Arguments for task_func

        Returns:
            job_id if successful, None if queue is full
        """
        if self.queue.qsize() >= self.max_queue_size:
            logger.warning("queue_full", username=username)
            return None

        job_id = f"job_{uuid.uuid4().hex[:12]}"

        self.jobs[job_id] = {
            "id": job_id,
            "username": username,
            "status": QueueStatus.PENDING,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "position": self.queue.qsize() + 1,
        }

        await self.queue.put(
            {
                "job_id": job_id,
                "task_func": task_func,
                "args": args,
                "kwargs": kwargs,
            }
        )

        logger.info("job_enqueued", job_id=job_id, username=username, position=self.jobs[job_id]["position"])
        return job_id

    async def _process_queue(self) -> None:
        """Queue processing loop"""
        while self.processing:
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                async with self.semaphore:
                    job_id = item["job_id"]
                    self.jobs[job_id]["status"] = QueueStatus.PROCESSING
                    self.jobs[job_id]["started_at"] = datetime.utcnow()

                    try:
                        result = await item["task_func"](*item["args"], **item["kwargs"])
                        self.jobs[job_id]["status"] = QueueStatus.COMPLETED
                        self.jobs[job_id]["result"] = result
                        logger.info("job_completed", job_id=job_id)

                    except Exception as e:
                        self.jobs[job_id]["status"] = QueueStatus.FAILED
                        self.jobs[job_id]["error"] = str(e)
                        logger.error("job_failed", job_id=job_id, error=str(e))

                    finally:
                        self.jobs[job_id]["completed_at"] = datetime.utcnow()
                        self.queue.task_done()

                    # Rate limiting between requests
                    await asyncio.sleep(1 / self.requests_per_second)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("queue_processor_error", error=str(e))

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status by ID"""
        job = self.jobs.get(job_id)
        if not job:
            return None

        # Calculate current queue position for pending jobs
        if job["status"] == QueueStatus.PENDING:
            position = self._get_queue_position(job_id)
            job_copy = job.copy()
            job_copy["queue_position"] = position
            job_copy["estimated_wait_seconds"] = position * (1 / self.requests_per_second)
            return job_copy

        return job

    def _get_queue_position(self, job_id: str) -> int:
        """Calculate position in queue"""
        position = 1
        # Access internal queue for position calculation
        for item in self.queue._queue:
            if item["job_id"] == job_id:
                return position
            position += 1
        return 0

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get overall queue statistics"""
        statuses = [j["status"] for j in self.jobs.values()]
        return {
            "total_pending": statuses.count(QueueStatus.PENDING),
            "total_processing": statuses.count(QueueStatus.PROCESSING),
            "total_completed": statuses.count(QueueStatus.COMPLETED),
            "total_failed": statuses.count(QueueStatus.FAILED),
            "queue_size": self.queue.qsize(),
            "processing_rate": f"{self.requests_per_second}/sec",
        }

    def should_queue(self) -> bool:
        """Determine if queueing is needed based on current load"""
        return self.queue.qsize() > 10


# Singleton instance
queue_manager = QueueManager()
