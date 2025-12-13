from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from flask import Flask, g
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

from app.config.settings import Settings


class Database:
    def __init__(self) -> None:
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def init_app(self, app: Flask, settings: Settings) -> None:
        engine = create_engine(
            settings.database_url,
            echo=settings.sqlalchemy_echo,
            pool_pre_ping=True,
            future=True,
        )

        self._engine = engine
        self._session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

        app.teardown_appcontext(self._teardown_request_session)

    def _teardown_request_session(self, exception: Optional[BaseException]) -> None:
        session: Optional[Session] = g.pop("db_session", None)
        if session is None:
            return

        try:
            if exception is None:
                session.commit()
            else:
                session.rollback()
        finally:
            session.close()

    def get_engine(self) -> Engine:
        if self._engine is None:
            raise RuntimeError("Database is not initialized. Call init_app first.")

        return self._engine

    def get_session(self) -> Session:
        existing: Optional[Session] = g.get("db_session")
        if existing is not None:
            return existing

        if self._session_factory is None:
            raise RuntimeError("Database is not initialized. Call init_app first.")

        session = self._session_factory()
        g.db_session = session
        return session

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session = self.get_session()
        try:
            yield session
        except Exception:
            session.rollback()
            raise

    def ping(self) -> bool:
        engine = self.get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True


