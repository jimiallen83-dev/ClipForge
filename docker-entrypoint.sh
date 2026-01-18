#!/bin/sh
set -e

echo "Running migrations or initializing DB..."
if [ -f /app/scripts/run_migrations.py ]; then
	echo "Found run_migrations.py - attempting alembic upgrade head"
	python /app/scripts/run_migrations.py upgrade head || echo "Migrations failed or skipped"
else
	echo "No migrations runner found; falling back to create_all"
	python - <<'PY'
from db import init_db
init_db()
print('DB initialized')
PY
fi

if [ "$1" = "worker" ]; then
	echo "Starting background worker..."
	exec python /app/worker.py
else
	echo "Starting uvicorn..."
	exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
fi
