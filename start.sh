#!/bin/bash
set -e

echo "Waiting for database..."
for i in $(seq 1 30); do
  python -c "
from config import settings
from sqlalchemy import create_engine, text
engine = create_engine(settings.database_url_with_ssl)
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
" 2>/dev/null && echo "Database ready" && break
  echo "Waiting for database... (attempt $i/30)"
  sleep 2
  if [ "$i" = "30" ]; then
    echo "Database not available after 30 attempts, exiting"
    exit 1
  fi
done

alembic upgrade head

if [ ! -d "Data/faiss_db" ]; then
    echo "Building FAISS index..."
    python utils/ingest.py
fi

exec uvicorn api:app --host 0.0.0.0 --port 8000
