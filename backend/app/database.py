"""Database engine and session handling (data layer)."""
from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _add_missing_columns(bind) -> None:
    """Add columns introduced after a table was first created.

    create_all() makes new tables but never changes existing ones, so a database
    made in Sprint 1 would miss later columns. New columns are always nullable,
    which makes adding them safe. (A team project that grows further should move
    to Alembic migrations.)
    """
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    with bind.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            present = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                col_type = column.type.compile(dialect=bind.dialect)
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'))


def init_db(bind=None) -> None:
    """Create tables that don't exist yet, and add any missing columns."""
    from app import models  # noqa: F401  (registers the models)

    bind = bind or engine
    _add_missing_columns(bind)
    Base.metadata.create_all(bind=bind)
