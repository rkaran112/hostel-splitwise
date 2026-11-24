"""
Database connection.

One setting decides which database we use: the DATABASE_URL environment variable.
    not set                     -> a local SQLite file (dev.db). Zero install, great on a laptop.
    postgresql://user:pw@host/db -> PostgreSQL (what the live app uses).

The rest of the code is identical for both. That is the point of SQLAlchemy.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Every table class in models.py inherits from this."""


def get_database_url():
    url = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")

    # Hosting sites give URLs starting with postgres:// or postgresql://.
    # SQLAlchemy needs to be told which Python driver to use: psycopg.
    for old_start in ("postgres://", "postgresql://"):
        if url.startswith(old_start):
            return "postgresql+psycopg://" + url[len(old_start):]
    return url


def make_engine(url):
    if url.startswith("sqlite"):
        # FastAPI handles requests on several threads; SQLite must be told that is fine.
        return create_engine(url, connect_args={"check_same_thread": False})
    # pool_pre_ping: test a connection before using it, because free hosts close idle ones.
    return create_engine(url, pool_pre_ping=True)


engine = make_engine(get_database_url())
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    """FastAPI hands one database session to each request, and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
