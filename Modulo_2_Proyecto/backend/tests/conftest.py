"""
Global test fixtures and configuration.

This module provides fixtures that are available to all tests.
"""
from __future__ import annotations

import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="session")
def db(app):
    """Create database for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope="function")
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session_obj = db.session
    session_obj.begin_nested()
    
    yield session_obj
    
    session_obj.close()
    transaction.rollback()
    connection.close()
