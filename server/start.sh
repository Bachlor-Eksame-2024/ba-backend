#!/bin/bash
set -e

# Function to check if postgres is ready
postgres_ready() {
    pg_isready -h postgres -p 5432 -U "$POSTGRES_USER"
}

until postgres_ready; do
  echo >&2 "Postgres is unavailable - sleeping"
  sleep 1
done

echo >&2 "Postgres is up - executing command"

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 3000 --reload