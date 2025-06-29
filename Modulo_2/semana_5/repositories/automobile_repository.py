"""
Automobile Repository for Lyfter Car Rental System
Handles all automobile-related database operations
"""

from typing import List, Dict, Any, Optional
from .base_repository import BaseRepository

class AutomobileRepository(BaseRepository):
    """Repository for automobile-related database operations"""
    
    def __init__(self):
        super().__init__()
        self.table_name = "automobiles"
        self.valid_statuses = ['available', 'rented', 'maintenance', 'retired']
    
    def create_automobile(self, automobile_data: Dict[str, Any]) -> Optional[Dict]:
        """Create a new automobile"""
        query = f"""
            INSERT INTO {self.get_table_name(self.table_name)} (
                make, model, year_manufactured, condition, status
            ) VALUES (
                %s, %s, %s, %s, %s
            ) RETURNING id, make, model, year_manufactured, condition, status, created_at, updated_at
        """
        
        params = (
            automobile_data['make'],
            automobile_data['model'],
            automobile_data['year_manufactured'],
            automobile_data['condition'],
            automobile_data.get('status', 'available')
        )
        
        return self.execute_command_returning(query, params)
    
    def get_automobile_by_id(self, automobile_id: int) -> Optional[Dict]:
        """Get automobile by ID"""
        query = f"""
            SELECT id, make, model, year_manufactured, condition, status, created_at, updated_at
            FROM {self.get_table_name(self.table_name)}
            WHERE id = %s
        """
        return self.execute_one(query, (automobile_id,))
    
    def get_available_automobiles(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict]:
        """Get all available automobiles"""
        where_clause, params = self.build_where_clause({'status': 'available'})
        pagination_clause = self.build_pagination_clause(limit, offset)
        
        query = f"""
            SELECT id, make, model, year_manufactured, condition, status, created_at, updated_at
            FROM {self.get_table_name(self.table_name)}
            {where_clause}
            ORDER BY make, model
            {pagination_clause}
        """
        
        return self.execute_query(query, tuple(params))
    
    def get_rented_automobiles(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict]:
        """Get all rented automobiles"""
        where_clause, params = self.build_where_clause({'status': 'rented'})
        pagination_clause = self.build_pagination_clause(limit, offset)
        
        query = f"""
            SELECT id, make, model, year_manufactured, condition, status, created_at, updated_at
            FROM {self.get_table_name(self.table_name)}
            {where_clause}
            ORDER BY make, model
            {pagination_clause}
        """
        
        return self.execute_query(query, tuple(params))
    
    def update_automobile_status(self, automobile_id: int, status: str) -> Optional[Dict]:
        """Update automobile status"""
        if status not in self.valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of: {self.valid_statuses}")
        
        query = f"""
            UPDATE {self.get_table_name(self.table_name)}
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, make, model, year_manufactured, condition, status, created_at, updated_at
        """
        return self.execute_command_returning(query, (status, automobile_id))
    
    def delete_automobile(self, automobile_id: int) -> bool:
        """Delete automobile by ID"""
        query = f"""
            DELETE FROM {self.get_table_name(self.table_name)}
            WHERE id = %s
        """
        rows_affected = self.execute_command(query, (automobile_id,))
        return rows_affected > 0
    
    def disable_automobile(self, automobile_id: int) -> Optional[Dict]:
        """Disable automobile (set status to retired)"""
        return self.update_automobile_status(automobile_id, 'retired')
    
    def get_automobile_stats(self) -> Dict[str, Any]:
        """Get automobile statistics"""
        query = f"""
            SELECT 
                COUNT(*) as total_automobiles,
                SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available_count,
                SUM(CASE WHEN status = 'rented' THEN 1 ELSE 0 END) as rented_count,
                SUM(CASE WHEN status = 'maintenance' THEN 1 ELSE 0 END) as maintenance_count,
                SUM(CASE WHEN status = 'retired' THEN 1 ELSE 0 END) as retired_count,
                MIN(year_manufactured) as oldest_year,
                MAX(year_manufactured) as newest_year,
                COUNT(DISTINCT make) as unique_makes,
                COUNT(DISTINCT model) as unique_models
            FROM {self.get_table_name(self.table_name)}
        """
        return self.execute_one(query) or {}
    
    def get_makes_and_models(self) -> Dict[str, List[str]]:
        """Get all makes and their corresponding models"""
        query = f"""
            SELECT DISTINCT make, model
            FROM {self.get_table_name(self.table_name)}
            ORDER BY make, model
        """
        
        results = self.execute_query(query)
        makes_models = {}
        
        for row in results:
            make = row['make']
            model = row['model']
            
            if make not in makes_models:
                makes_models[make] = []
            
            if model not in makes_models[make]:
                makes_models[make].append(model)
        
        return makes_models 