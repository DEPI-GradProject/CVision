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

if [ ! -f "Data/faiss_db/index.faiss" ]; then
    if [ -f "Data/jobs.csv" ]; then
        echo "Building FAISS index..."
        python utils/ingest.py
        if [ $? -ne 0 ]; then
            echo "FAISS build failed, but continuing..."
        fi
    else
        echo "Skipping FAISS build: Data/jobs.csv not found"
        echo "WARNING: Job matching features will fail until the FAISS index is built."
    fi
fi

exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
