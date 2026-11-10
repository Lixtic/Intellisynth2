from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import config

SQLALCHEMY_DATABASE_URL = "sqlite:///./logs.db"

Base = declarative_base()

if config.is_sqlite():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None

    def SessionLocal():  # type: ignore[misc]
        raise RuntimeError("SQLite backend is disabled in Firebase-only mode")
