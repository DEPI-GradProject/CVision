import subprocess
import sys

from sqlalchemy import create_engine

from config import settings

if not settings.database_url:
    raise ValueError("DATABASE_URL is missing. Please check your .env file.")

engine = create_engine(settings.database_url_with_ssl, echo=True)


def init_db():
    print("Running Alembic migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Alembic migration failed:\n{result.stderr}")
        raise RuntimeError("Database migration failed")
    print("Database is up to date.")


if __name__ == "__main__":
    init_db()
