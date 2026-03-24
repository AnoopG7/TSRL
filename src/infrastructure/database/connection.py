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
    This ensures schema changes always go through the migration system.
    Fails fast if alembic is unavailable instead of bypassing migrations.
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
            # Fail fast - don't bypass migrations with create_all
            raise RuntimeError(
                f"Alembic migration failed: {result.stderr}\n"
                "Run 'alembic upgrade head' manually or check your migration setup."
            )
    except FileNotFoundError as e:
        # Alembic not installed
        raise RuntimeError(
            "Alembic is not installed. Install it with: pip install alembic\n"
            "Database migrations require alembic to be available."
        ) from e
    except Exception as e:
        # Re-raise any other exceptions - don't silently fallback to create_all
        raise RuntimeError(f"Database initialization failed: {e}") from e
