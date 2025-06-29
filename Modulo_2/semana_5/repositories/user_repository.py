"""
User Repository for Lyfter Car Rental System 
Handles all user-related database operations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_repository import BaseRepository

class UserRepository(BaseRepository):
    """Repository for user-related database operations"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "users"
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new user"""
        query = f"""
            INSERT INTO {self.get_table_name(self.table_name)} (
                name, email, username, password, date_of_birth, account_state
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            ) RETURNING id, name, email, username, date_of_birth, account_state, created_at, updated_at
        """
        
        params = (
            user_data['name'],
            user_data['email'],
            user_data['username'],
            user_data['password'],
            user_data.get('date_of_birth'),
            user_data.get('account_state', True)
        )
        
        return self.execute_command_returning(query, params)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = f"""
            SELECT id, name, email, username, date_of_birth, account_state, created_at, updated_at
            FROM {self.get_table_name(self.table_name)}
            WHERE id = %s
        """
        return self.execute_one(query, (user_id,))
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = f"""
            SELECT id, name, email, username, date_of_birth, account_state, created_at, updated_at
            FROM {self.get_table_name(self.table_name)}
            WHERE email = %s
        """
        return self.execute_one(query, (email,))
    
    def update_user_status(self, user_id: int, account_state: bool) -> Optional[Dict]:
        """Update user account status"""
        query = f"""
            UPDATE {self.get_table_name(self.table_name)}
            SET account_state = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, name, email, username, date_of_birth, account_state, created_at, updated_at
        """
        return self.execute_command_returning(query, (account_state, user_id))
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user by ID"""
        query = f"""
            DELETE FROM {self.get_table_name(self.table_name)}
            WHERE id = %s
        """
        rows_affected = self.execute_command(query, (user_id,))
        return rows_affected > 0
    
    def user_exists(self, email: str = None, username: str = None) -> bool:
        """Check if user exists by email or username"""
        filters = {}
        if email:
            filters['email'] = email
        if username:
            filters['username'] = username
        
        return self.record_exists(self.table_name, filters)
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        query = f"""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN account_state = true THEN 1 ELSE 0 END) as active_users,
                SUM(CASE WHEN account_state = false THEN 1 ELSE 0 END) as inactive_users,
                MIN(created_at) as first_user_created,
                MAX(created_at) as last_user_created
            FROM {self.get_table_name(self.table_name)}
        """
        return self.execute_one(query) or {} 