"""
Base Repository for Lyfter Car Rental System
Implements common database operations and connection management
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

# Load environment variables
load_dotenv()

class BaseRepository:
    """Base repository class with common database operations"""
    
    def __init__(self):
        """Initialize database configuration"""
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'lyfter_car_rental'),
        }
        self.schema_name = os.getenv('DB_SCHEMA', 'lyfter_car_rental')
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=int(self.db_config['port']),
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            yield cursor
        except psycopg2.Error as e:
            conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
    
    def execute_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict]:
        """Execute a SELECT query and return first result"""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return dict(result) if result else None
    
    def execute_command(self, query: str, params: Optional[Tuple] = None) -> int:
        """Execute INSERT, UPDATE, or DELETE command"""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cursor:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
                
    def execute_command_returning(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict]:
        """Execute INSERT, UPDATE, or DELETE with RETURNING clause"""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cursor:
                cursor.execute(query, params)
                conn.commit()
                result = cursor.fetchone()
                return dict(result) if result else None
    
    def build_where_clause(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """Build WHERE clause from filters dictionary"""
        if not filters:
            return "", []
        
        conditions = []
        params = []
        
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, str) and '%' in value:
                    conditions.append(f"{key} LIKE %s")
                else:
                    conditions.append(f"{key} = %s")
                params.append(value)
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return where_clause, params
    
    def build_pagination_clause(self, limit: Optional[int] = None, offset: Optional[int] = None) -> str:
        """Build LIMIT and OFFSET clause"""
        clause = ""
        if limit:
            clause += f" LIMIT {limit}"
        if offset:
            clause += f" OFFSET {offset}"
        return clause
    
    def get_table_name(self, table: str) -> str:
        """Get fully qualified table name with schema"""
        return f'"{self.schema_name}".{table}'
    
    def count_records(self, table: str, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records in table with optional filters"""
        where_clause, params = self.build_where_clause(filters or {})
        query = f"SELECT COUNT(*) as count FROM {self.get_table_name(table)}{where_clause}"
        
        result = self.execute_one(query, tuple(params))
        return result['count'] if result else 0
    
    def record_exists(self, table: str, filters: Dict[str, Any]) -> bool:
        """Check if record exists with given filters"""
        return self.count_records(table, filters) > 0 