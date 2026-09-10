#!/bin/sh
set -e

DB_PATH="${KTU_DB_PATH:-/app/database/ktu.db}"
mkdir -p "$(dirname "$DB_PATH")"

if [ ! -f "$DB_PATH" ]; then
  echo "No existing database at $DB_PATH — seeding from the image's baked-in copy."
  cp /app/seed-data/ktu.db "$DB_PATH"
fi

python database/migrate.py
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
