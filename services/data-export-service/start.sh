#!/bin/bash
set -e
echo "Waiting for database..."
sleep 5
echo "Running migrations..."
cd /app
export DATABASE_URL="mysql+pymysql://root:rootpassword@mysql:3306/energy_export_db"
python -m alembic upgrade head
echo "Starting service..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
