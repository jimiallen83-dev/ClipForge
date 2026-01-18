"""RQ worker runner that registers job functions and starts worker.

This script is intended to be run in a container or developer machine.
"""

import os
from rq import Queue, Worker, SimpleWorker
from redis import Redis

# Import task functions you want to enqueue

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)

if __name__ == "__main__":
    # Create queue and worker using explicit Redis connection to avoid
    # relying on `Connection` context which may be located differently
    # across `rq` versions.
    q = Queue(connection=redis_conn)
    # On Windows (no fork) use SimpleWorker to avoid os.fork usage in Worker
    if os.name == "nt" or not hasattr(os, "fork"):
        worker = SimpleWorker([q], connection=redis_conn)
    else:
        worker = Worker([q], connection=redis_conn)
    worker.work()
