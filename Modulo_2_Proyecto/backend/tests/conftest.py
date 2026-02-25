"""
Global test fixtures and configuration.

This module provides fixtures that are available to all tests.
"""
from __future__ import annotations

import os

# Set TESTING environment variable BEFORE any other imports that might trigger settings loading
os.environ["TESTING"] = "true"

import pytest
from app import create_app
from app.extensions import db as _db
from app.domain.common.models import Base
from app.domain.users.models import User
from app.domain.auth.models import AuthRefreshToken
from app.domain.games.models import Game
from app.domain.games.ruleset_models import RulesetTemplate
import sqlalchemy as sa


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    # Ensure settings cache is clear for tests to pick up TESTING=true
    from app.config import get_settings
    get_settings.cache_clear()
    
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="session")
def db(app):
    """Create database for testing."""
    # Bypass safety guards for DDL operations
    os.environ["ALLOW_DESTRUCTIVE_DDL"] = "true"
    
    with app.app_context():
        engine = _db.get_engine()
        # Drop and recreate all tables to ensure schema is up to date
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        yield _db


@pytest.fixture(scope="function")
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="function")
def session(app, db):
    """Create a new database session for a test."""
    with app.app_context():
        # Clear g.db_session if it exists from a previous test
        from flask import g
        g.pop("db_session", None)
        
        session_obj = db.get_session()
        yield session_obj
        # session will be closed/rolled back by app.teardown_appcontext

@pytest.fixture(scope="function")
def test_users():
    """A list to track users created during a test for manual cleanup if needed."""
    return []

@pytest.fixture(scope="function", autouse=False)
def cleanup_database(app, db, session):
    """Automatically clean up the database before and after each test.
    
    Uses the SAME session as the test to avoid deadlocks.
    All child tables use ON DELETE CASCADE, so deleting parents cleans everything.
    """
    def _clean(sess):
        # Bypass safety guards for cleanup
        os.environ["ALLOW_UNSAFE_QUERY"] = "true"
        os.environ["ALLOW_DESTRUCTIVE_DDL"] = "true"
        
        # Delete parents - CASCADE handles children automatically
        sess.query(Game).delete()
        sess.query(RulesetTemplate).delete()
        sess.query(AuthRefreshToken).delete()
        sess.query(User).delete()
        sess.commit()
    
    _clean(session)
    yield
    _clean(session)
