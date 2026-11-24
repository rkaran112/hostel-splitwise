"""
Test setup shared by every test file.

The API tests use a throwaway database, never your real dev.db.
    default                     -> a temporary SQLite file
    TEST_DATABASE_URL is set    -> that database (CI points it at a real PostgreSQL)

The environment variable must be set BEFORE app.db is imported, because app.db
creates its engine the moment it is imported.
"""

import os
import tempfile

TEST_URL = os.environ.get("TEST_DATABASE_URL")
if TEST_URL is None:
    TEST_URL = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db").replace("\\", "/")
os.environ["DATABASE_URL"] = TEST_URL

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402,F401  (importing it registers the tables)
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    """A test client with empty tables, so every test starts from scratch."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return TestClient(app)
