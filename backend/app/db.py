from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    # Neon's free-tier serverless Postgres auto-suspends its compute after a
    # few minutes of idle. Cached SQLAlchemy connections then die server-side
    # and the next checkout raises "SSL connection has been closed
    # unexpectedly". `pool_pre_ping` issues a lightweight SELECT 1 before
    # each checkout — dead connections are discarded and reopened.
    # Harmless on SQLite (also benefits long-lived processes).
    pool_pre_ping=not _is_sqlite,
    # Recycle connections older than 5 min so we don't outlive Neon's
    # idle suspend window even when ping somehow misses it.
    pool_recycle=300 if not _is_sqlite else -1,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
