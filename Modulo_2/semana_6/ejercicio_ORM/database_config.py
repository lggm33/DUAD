import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Database configuration
DATABASE_NAME = "database.db"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), DATABASE_NAME)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def validate_sqlalchemy_setup():
    """Validate SQLAlchemy setup and show version"""
    import sqlalchemy
    print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    print("SQLAlchemy setup completed successfully!")
    return sqlalchemy.__version__

def get_database_path():
    """Get the database file path"""
    return DATABASE_PATH

def get_session():
    """Get a new database session"""
    return Session()

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close() 