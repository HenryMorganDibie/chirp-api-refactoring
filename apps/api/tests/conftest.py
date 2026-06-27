"""Test configuration and fixtures for Chirp API tests.

Creates an in-memory SQLite database for test isolation.
Provides a session fixture that creates fresh tables per test.
"""

import os

# Must be set before any chirp_api import, as auth.py reads it at module load.
os.environ.setdefault("GRPC_JWT_SECRET", "test-jwt-secret-for-unit-tests-32chars!")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chirp_api.db.models import Base


@pytest.fixture
def session(monkeypatch):
    """Create a fresh in-memory SQLite session for each test.

    All tables are created fresh. The session is closed after the test.
    Also monkey-patches chirp_api.db.SessionLocal so handlers use the test DB.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    test_session = TestSession()

    # Monkey-patch SessionLocal so handlers use our test session
    import chirp_api.db as db_module

    monkeypatch.setattr(db_module, "SessionLocal", TestSession)

    yield test_session

    test_session.close()
    engine.dispose()
