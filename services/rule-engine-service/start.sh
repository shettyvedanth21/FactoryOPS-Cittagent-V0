#!/bin/bash
set -e
echo "Waiting for database..."
sleep 5
echo "Running migrations..."
cd /app
alembic upgrade head
echo "Starting service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8002
