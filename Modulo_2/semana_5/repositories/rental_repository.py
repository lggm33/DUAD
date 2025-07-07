"""
Rental Repository for Lyfter Car Rental System
Handles all rental-related database operations including relationships
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from .base_repository import BaseRepository

class RentalRepository(BaseRepository):
    """Repository for rental-related database operations"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "rentals"
        self.valid_statuses = ['active', 'completed', 'overdue', 'cancelled']
    
    def create_rental(self, rental_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new rental"""
        query = f"""
            INSERT INTO {self.get_table_name(self.table_name)} (
                user_id, automobile_id, expected_return_date, daily_rate, total_cost
            ) VALUES (
                %s, %s, %s, %s, %s
            ) RETURNING id, user_id, automobile_id, rental_date, expected_return_date, 
                       actual_return_date, rental_status, daily_rate, total_cost, created_at, updated_at
        """
        
        params = (
            rental_data['user_id'],
            rental_data['automobile_id'],
            rental_data['expected_return_date'],
            rental_data['daily_rate'],
            rental_data['total_cost']
        )
        
        return self.execute_command_returning(query, params)
    
    def get_rental_by_id(self, rental_id: int) -> Optional[Dict]:
        """Get rental by ID with user and automobile details"""
        query = f"""
            SELECT 
                r.id, r.user_id, r.automobile_id, r.rental_date, r.expected_return_date,
                r.actual_return_date, r.rental_status, r.daily_rate, r.total_cost,
                r.created_at, r.updated_at,
                u.name as user_name, u.email as user_email,
                a.make as automobile_make, a.model as automobile_model,
                a.year_manufactured as automobile_year
            FROM {self.get_table_name(self.table_name)} r
            LEFT JOIN {self.get_table_name('users')} u ON r.user_id = u.id
            LEFT JOIN {self.get_table_name('automobiles')} a ON r.automobile_id = a.id
            WHERE r.id = %s
        """
        return self.execute_one(query, (rental_id,))
    
    def get_active_rentals(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict]:
        """Get all active rentals"""
        where_clause, params = self.build_where_clause({'r.rental_status': 'active'})
        pagination_clause = self.build_pagination_clause(limit, offset)
        
        query = f"""
            SELECT 
                r.id, r.user_id, r.automobile_id, r.rental_date, r.expected_return_date,
                r.actual_return_date, r.rental_status, r.daily_rate, r.total_cost,
                r.created_at, r.updated_at,
                u.name as user_name, u.email as user_email,
                a.make as automobile_make, a.model as automobile_model,
                a.year_manufactured as automobile_year
            FROM {self.get_table_name(self.table_name)} r
            LEFT JOIN {self.get_table_name('users')} u ON r.user_id = u.id
            LEFT JOIN {self.get_table_name('automobiles')} a ON r.automobile_id = a.id
            {where_clause}
            ORDER BY r.rental_date DESC
            {pagination_clause}
        """
        
        return self.execute_query(query, tuple(params))
    
    def get_overdue_rentals(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict]:
        """Get all overdue rentals"""
        where_clause, params = self.build_where_clause({'r.rental_status': 'overdue'})
        pagination_clause = self.build_pagination_clause(limit, offset)
        
        query = f"""
            SELECT 
                r.id, r.user_id, r.automobile_id, r.rental_date, r.expected_return_date,
                r.actual_return_date, r.rental_status, r.daily_rate, r.total_cost,
                r.created_at, r.updated_at,
                u.name as user_name, u.email as user_email,
                a.make as automobile_make, a.model as automobile_model,
                a.year_manufactured as automobile_year
            FROM {self.get_table_name(self.table_name)} r
            LEFT JOIN {self.get_table_name('users')} u ON r.user_id = u.id
            LEFT JOIN {self.get_table_name('automobiles')} a ON r.automobile_id = a.id
            {where_clause}
            ORDER BY r.rental_date DESC
            {pagination_clause}
        """
        
        return self.execute_query(query, tuple(params))
    
    def complete_rental(self, rental_id: int, actual_return_date: Optional[datetime] = None) -> Optional[Dict]:
        """Complete a rental and update automobile status"""
        if actual_return_date is None:
            actual_return_date = datetime.now()
        
        # Use transaction to ensure both operations succeed
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cursor:
                try:
                    # Update rental status
                    cursor.execute(f"""
                        UPDATE {self.get_table_name(self.table_name)}
                        SET rental_status = 'completed', 
                            actual_return_date = %s, 
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s AND rental_status = 'active'
                        RETURNING id, user_id, automobile_id, rental_date, expected_return_date,
                                  actual_return_date, rental_status, daily_rate, total_cost, 
                                  created_at, updated_at
                    """, (actual_return_date, rental_id))
                    
                    rental_result = cursor.fetchone()
                    if not rental_result:
                        return None
                    
                    # Update automobile status to available
                    cursor.execute(f"""
                        UPDATE {self.get_table_name('automobiles')}
                        SET status = 'available', updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (rental_result['automobile_id'],))
                    
                    conn.commit()
                    return dict(rental_result)
                    
                except Exception as e:
                    conn.rollback()
                    raise e
    
    def delete_rental(self, rental_id: int) -> bool:
        """Delete rental by ID (only if cancelled or completed)"""
        query = f"""
            DELETE FROM {self.get_table_name(self.table_name)}
            WHERE id = %s AND rental_status IN ('cancelled', 'completed')
        """
        rows_affected = self.execute_command(query, (rental_id,))
        return rows_affected > 0
    
    def get_rental_stats(self) -> Dict[str, Any]:
        """Get rental statistics"""
        query = f"""
            SELECT 
                COUNT(*) as total_rentals,
                SUM(CASE WHEN rental_status = 'active' THEN 1 ELSE 0 END) as active_count,
                SUM(CASE WHEN rental_status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                SUM(CASE WHEN rental_status = 'overdue' THEN 1 ELSE 0 END) as overdue_count,
                SUM(CASE WHEN rental_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_count,
                AVG(daily_rate) as average_daily_rate,
                SUM(total_cost) as total_revenue,
                AVG(total_cost) as average_rental_cost,
                MIN(rental_date) as first_rental_date,
                MAX(rental_date) as last_rental_date
            FROM {self.get_table_name(self.table_name)}
        """
        return self.execute_one(query) or {} 