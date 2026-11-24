from app.db import get_database_url


def test_default_is_a_local_sqlite_file(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert get_database_url() == "sqlite:///./dev.db"


def test_hosting_site_postgres_urls_get_the_psycopg_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@host:5432/db")
    assert get_database_url() == "postgresql+psycopg://user:pw@host:5432/db"

    monkeypatch.setenv("DATABASE_URL", "postgres://user:pw@host:5432/db")
    assert get_database_url() == "postgresql+psycopg://user:pw@host:5432/db"


def test_other_urls_are_left_alone(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///other.db")
    assert get_database_url() == "sqlite:///other.db"
