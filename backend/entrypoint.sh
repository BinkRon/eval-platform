#!/bin/sh
set -e
trap 'echo "[entrypoint] Migration failed. Container will exit."; exit 1' ERR

echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1}
