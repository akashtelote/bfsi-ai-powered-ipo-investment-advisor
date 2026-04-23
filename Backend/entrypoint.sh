#!/usr/bin/env bash
set -e

# Strip SQLAlchemy dialect prefix to get the raw filesystem path
DB_PATH="${DATABASE_URL#sqlite+aiosqlite:///}"

if [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] Database not found — seeding from /app/data/seed_db.py ..."
  python /app/data/seed_db.py || echo "[entrypoint] Seed failed or skipped — continuing"
else
  echo "[entrypoint] Database exists — skipping seed"
fi

exec "$@"
