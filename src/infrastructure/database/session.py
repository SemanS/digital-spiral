"""Database session management."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool


def get_database_url() -> str:
    """
    Get database URL from environment variable.

    Returns:
        Database URL string

    Raises:
        ValueError: If DATABASE_URL is not set
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please set it in your .env file or environment."
        )
    return database_url


def create_database_engine(
    database_url: str | None = None,
    echo: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_pre_ping: bool = True,
    use_null_pool: bool = False,
) -> Engine:
    """
    Create SQLAlchemy engine with appropriate configuration.

    Args:
        database_url: Database URL (defaults to DATABASE_URL env var)
        echo: Whether to log SQL statements
        pool_size: Number of connections to maintain in the pool
        max_overflow: Maximum number of connections to create beyond pool_size
        pool_pre_ping: Test connections before using them
        use_null_pool: Use NullPool (for testing or serverless)

    Returns:
        SQLAlchemy Engine instance
    """
    if database_url is None:
        database_url = get_database_url()

    # Determine pool class
    poolclass = NullPool if use_null_pool else QueuePool

    # Create engine
    engine = create_engine(
        database_url,
        echo=echo,
        poolclass=poolclass,
        pool_size=pool_size if not use_null_pool else None,
        max_overflow=max_overflow if not use_null_pool else None,
        pool_pre_ping=pool_pre_ping,
        # PostgreSQL-specific settings
        connect_args={
            "options": "-c timezone=utc",  # Use UTC timezone
        },
    )

    # Register event listeners
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Set up connection-level settings."""
        # Set statement timeout (30 seconds)
        with dbapi_conn.cursor() as cursor:
            cursor.execute("SET statement_timeout = '30s'")

    return engine


def create_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """
    Create SQLAlchemy session factory.

    Args:
        engine: SQLAlchemy engine (creates new one if not provided)

    Returns:
        Session factory
    """
    if engine is None:
        engine = create_database_engine()

    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


# Global session factory (initialized on first use)
_session_factory: sessionmaker[Session] | None = None


def get_session_factory() -> sessionmaker[Session]:
    """
    Get or create global session factory.

    Returns:
        Session factory
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory()
    return _session_factory


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        SQLAlchemy Session

    Example:
        ```python
        with get_db_session() as session:
            user = session.query(User).first()
            print(user.name)
        ```
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to inject database session.

    Yields:
        SQLAlchemy Session

    Example:
        ```python
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


__all__ = [
    "get_database_url",
    "create_database_engine",
    "create_session_factory",
    "get_session_factory",
    "get_db_session",
    "get_db",
]

