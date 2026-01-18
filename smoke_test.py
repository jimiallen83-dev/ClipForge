import os
import sys
import time

# Ensure project root on path
sys.path.insert(0, os.path.dirname(__file__))

from scripts.run_migrations import main as run_migrations_main  # noqa: E402


def run_migrations():
    print("Running migrations (upgrade head)")
    try:
        run_migrations_main(["upgrade", "head"])
    except SystemExit as e:
        if e.code != 0:
            raise


def hit_health():
    print("Importing FastAPI app and hitting /health...")
    from fastapi.testclient import TestClient
    import app as app_module

    client = TestClient(app_module.app)
    r = client.get("/health")
    print("health status:", r.status_code, r.json())
    if r.status_code != 200:
        raise RuntimeError("Health check failed")


if __name__ == "__main__":
    run_migrations()
    # give DB a tiny moment
    time.sleep(0.5)
    hit_health()
    print("Smoke test passed")
