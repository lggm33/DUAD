import os
import sqlite3
from database_config import Base, engine, get_database_path, get_session
from models import User, Address, Automobile

def check_database_exists() -> bool:
    """Check if database file exists"""
    return os.path.exists(get_database_path())

def create_database_if_not_exists():
    """Create database file if it doesn't exist"""
    database_path = get_database_path()
    if not check_database_exists():
        print(f"Database file not found. Creating new database at: {database_path}")
        # Create empty database file
        conn = sqlite3.connect(database_path)
        conn.close()
        print("Database file created successfully!")
    else:
        print(f"Database file already exists at: {database_path}")

def check_and_create_tables():
    """Check if tables exist and create them if they don't"""
    try:
        # Check if tables exist by trying to query them
        session = get_session()
        session.query(User).first()
        session.query(Address).first()
        session.query(Automobile).first()
        session.close()
        print("All tables already exist in the database.")
    except Exception as e:
        print("Tables don't exist. Creating them...")
        Base.metadata.create_all(engine)  # type: ignore
        print("Tables created successfully!")

def setup_database():
    """Complete database setup process"""
    create_database_if_not_exists()
    check_and_create_tables()
    print("Database setup completed!") 