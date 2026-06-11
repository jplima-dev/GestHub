from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import settings


settings.database_path.parent.mkdir(parents=True, exist_ok=True)
settings.upload_dir.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_runtime_migrations()


def ensure_runtime_migrations() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as connection:
        user_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(usuarios)")).all()}
        if "avatar_path" not in user_columns:
            connection.execute(text("ALTER TABLE usuarios ADD COLUMN avatar_path VARCHAR(255)"))

        aviso_columns = {row[1] for row in connection.execute(text("PRAGMA table_info(avisos)")).all()}
        if "imovel_id" not in aviso_columns:
            connection.execute(text("ALTER TABLE avisos ADD COLUMN imovel_id INTEGER"))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
