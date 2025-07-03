#!/usr/bin/env python3
"""
Database Configuration Base Class for Lyfter Car Rental System
- Centralizes database connection configuration
- Provides common database operations for setup classes
- Eliminates code duplication across setup classes
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv()

class DatabaseConfig:
    """Base class for database configuration and common operations"""
    
    def __init__(self):
        """Initialize database configuration from environment variables"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.db_name = os.getenv('DB_NAME', 'lyfter_car_rental')
        self.schema_name = os.getenv('DB_SCHEMA', 'lyfter_car_rental')
        
        # Database configuration dictionary for convenience
        self.db_config = {
            'host': self.host,
            'port': int(self.port),
            'user': self.user,
            'password': self.password,
            'database': self.db_name
        }
    
    @contextmanager
    def get_connection(self, database=None, autocommit=False):
        """
        Context manager for database connections
        
        Args:
            database: Database name (defaults to configured database)
            autocommit: Whether to use autocommit mode
        """
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=int(self.port),
                user=self.user,
                password=self.password,
                database=database or self.db_name
            )
            
            if autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, conn):
        """Context manager for database cursors"""
        cursor = None
        try:
            cursor = conn.cursor()
            yield cursor
        except psycopg2.Error as e:
            conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
    
    def get_postgres_connection(self):
        """Get connection to postgres default database (for admin operations)"""
        return psycopg2.connect(
            host=self.host,
            port=int(self.port),
            user=self.user,
            password=self.password,
            database='postgres'
        )
    
    def get_project_connection(self):
        """Get connection to project database"""
        return psycopg2.connect(
            host=self.host,
            port=int(self.port),
            user=self.user,
            password=self.password,
            database=self.db_name
        )
    
    def table_exists(self, table_name):
        """Check if a table exists in the schema"""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s 
                        AND table_name = %s
                    );
                """, (self.schema_name, table_name))
                
                result = cursor.fetchone()
                return result[0] if result else False
    
    def count_table_records(self, table_name):
        """Count records in a table"""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cursor:
                cursor.execute(f'SELECT COUNT(*) FROM "{self.schema_name}".{table_name}')
                result = cursor.fetchone()
                return result[0] if result else 0
    
    def get_qualified_table_name(self, table_name):
        """Get fully qualified table name with schema"""
        return f'"{self.schema_name}".{table_name}'
    
    def print_config_info(self):
        """Print database configuration information"""
        print(f"📊 Database Configuration:")
        print(f"   • Host: {self.host}")
        print(f"   • Port: {self.port}")
        print(f"   • User: {self.user}")
        print(f"   • Database: {self.db_name}")
        print(f"   • Schema: {self.schema_name}")
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except psycopg2.Error:
            return False
    
    def handle_setup_error(self, error, operation_name):
        """Handle setup errors with consistent messaging"""
        print(f"⚠️  Warning {operation_name}: {error}")
        print("✅ Continuing with setup...")
        return True  # Continue even if there's an error 