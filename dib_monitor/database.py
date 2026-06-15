from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .models import Base

_engine = None


def get_engine(db_url: str = "sqlite:///./dib_monitor.db"):
    global _engine
    if _engine is None:
        _engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return _engine


def init_db(db_url: str = "sqlite:///./dib_monitor.db"):
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine


def get_db():
    engine = get_engine()
    with Session(engine) as session:
        yield session
