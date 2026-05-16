from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=settings.sql_echo, connect_args=connect_args)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
