from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.paths import ensure_data_dirs
from app.db.models import Base


def make_engine():
    ensure_data_dirs()
    connect_args = {"check_same_thread": False} if get_settings().database_url.startswith("sqlite") else {}
    return create_engine(get_settings().database_url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    if not get_settings().database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("tasks")}
    required = {
        "pack_identity_json": "TEXT",
        "official_candidates_json": "TEXT",
        "report": "TEXT",
    }
    with engine.begin() as connection:
        for name, column_type in required.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE tasks ADD COLUMN {name} {column_type}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
