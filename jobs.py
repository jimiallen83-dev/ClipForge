from fastapi import APIRouter, HTTPException
from rq import Queue
from rq.job import Job
from redis import Redis
import os

router = APIRouter(prefix="/jobs")

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)
queue = Queue(connection=redis_conn)


@router.get("/{job_id}")
def job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job.get_id(), "status": job.get_status(), "result": str(job.result)}
