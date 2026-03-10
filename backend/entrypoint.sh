#!/bin/sh
set -e

echo "Running database migrations..."
if ! alembic upgrade head; then
    echo "[entrypoint] Migration failed. Container will exit."
    exit 1
fi

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1}
