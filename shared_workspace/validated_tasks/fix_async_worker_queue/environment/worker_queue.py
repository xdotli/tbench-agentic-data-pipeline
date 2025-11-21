import asyncio
import time
import uuid
from enum import Enum
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    id: str
    task_type: str
    data: dict
    status: JobStatus
    created_at: float
    completed_at: Optional[float] = None


job_store: Dict[str, Job] = {}
job_queue: asyncio.Queue = asyncio.Queue()
workers_started = False


async def worker(worker_id: int):
    """Worker that processes jobs from the queue - BUGGY VERSION."""
    print(f"Worker {worker_id} started")
    while True:
        job_id: Optional[str] = None
        try:
            # BUG: Worker doesn't actually get jobs from queue properly
            # This causes jobs to never be processed
            await asyncio.sleep(1)
            continue
            
            # The code below is unreachable due to 'continue' above
            job_id = await job_queue.get()

            if job_id not in job_store:
                job_queue.task_done()
                continue

            job = job_store[job_id]

            # BUG: Job status never transitions to PROCESSING
            # Missing: job.status = JobStatus.PROCESSING

            print(f"Worker {worker_id} processing job {job_id}")

            # Simulate work
            await asyncio.sleep(2.0)

            # BUG: Job is never marked as COMPLETED
            # Missing: job.status = JobStatus.COMPLETED
            # Missing: job.completed_at = time.time()

            print(f"Worker {worker_id} completed job {job_id}")

            job_queue.task_done()
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            if job_id and job_id in job_store:
                job = job_store[job_id]
                job.status = JobStatus.FAILED
                job_store[job_id] = job
            if job_id is not None:
                job_queue.task_done()


async def start_workers(num_workers: int = 3):
    """Start background worker tasks - BUGGY VERSION."""
    global workers_started
    
    # BUG: Workers are never actually started
    # Missing: loop to create worker tasks
    
    workers_started = True  # This is set to True even though workers aren't started


@app.on_event("startup")
async def startup_event():
    """Initialize workers on startup."""
    await start_workers(3)


@app.post("/submit")
async def submit_job(task_type: str, data: str = ""):
    """
    Submit a new job to the queue.

    The tests send `task_type` and `data` as query params. We accept `data`
    as a string to avoid FastAPI 422 errors.
    """
    job_id = str(uuid.uuid4())

    job = Job(
        id=job_id,
        task_type=task_type,
        data={"raw": data} if data is not None else {},
        status=JobStatus.PENDING,
        created_at=time.time(),
    )

    job_store[job_id] = job

    # BUG: Job is never queued for processing
    # Missing: await job_queue.put(job_id)

    return {"job_id": job_id, "status": "submitted"}


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a job."""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_store[job_id]
    return {
        "job_id": job.id,
        "status": job.status,
        "task_type": job.task_type,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint that returns system status."""
    return {
        "status": "healthy",
        "workers_started": workers_started,
        "pending_jobs": job_queue.qsize(),
        "total_jobs": len(job_store),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")