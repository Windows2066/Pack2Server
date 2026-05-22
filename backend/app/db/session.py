from sqlalchemy import create_engine
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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
