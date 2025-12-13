#!/bin/bash
set -e

echo "Starting application..."

if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL is not set!"
    exit 1
fi

echo "Waiting for database to be ready..."
python << 'EOF'
import time
import psycopg2
import os

url = os.environ["DATABASE_URL"]
max_retries = 30

for i in range(max_retries):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print("Database is ready!")
        break
    except psycopg2.OperationalError as e:
        print(f"Waiting for database... ({i+1}/{max_retries})")
        time.sleep(2)
else:
    print("ERROR: Could not connect to database after 30 attempts!")
    exit(1)
EOF

echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
