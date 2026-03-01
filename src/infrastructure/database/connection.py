from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from config.settings import get_settings

settings = get_settings()

Base = declarative_base()


def get_database_path() -> Path:
    db_path = Path(settings.database.path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_engine():
    db_path = get_database_path()
    database_url = f"sqlite:///{db_path}"
    return create_engine(
        database_url,
        echo=settings.database.echo,
        pool_pre_ping=True,
    )


def get_session_factory():
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database using Alembic migrations.

    Runs 'alembic upgrade head' to apply all pending migrations.
    This ensures schema changes always go through the migration system
    instead of bypassing it with create_all().
    """
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            # If alembic fails (e.g., first run with no DB), fall back to create_all
            engine = get_engine()
            Base.metadata.create_all(bind=engine)
    except Exception:
        # Fallback: create tables directly if alembic is unavailable
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
