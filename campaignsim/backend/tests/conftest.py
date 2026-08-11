"""Shared pytest fixtures for CampaignSim backend tests."""

import os
import pytest

# Point at an in-memory SQLite database for fast, isolated tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-tests-only")
os.environ.setdefault("JWT_ACCESS_TTL_MINUTES", "15")
os.environ.setdefault("JWT_REFRESH_TTL_DAYS", "30")
os.environ.setdefault("LLM_API_KEY", "test-key")


@pytest.fixture()
def app():
    from app import create_app
    from app.extensions import db as _db

    application = create_app()
    application.config["TESTING"] = True
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    from app.extensions import db as _db
    yield _db.session
