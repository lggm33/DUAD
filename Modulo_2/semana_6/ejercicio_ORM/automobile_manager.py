from typing import List, Optional
from database_config import session_scope
from models import Automobile

class AutomobileManager:
    """Class for managing automobile operations"""
    
    def __init__(self):
        # No longer maintaining a persistent session
        pass
    
    # Requirement 4.2: Create/Update/Delete a new automobile
    def create_automobile(self, brand: str, model: str, year: int, color: str, 
                         license_plate: str, user_id: Optional[int] = None) -> Automobile:
        """Create a new automobile"""
        with session_scope() as session:
            automobile = Automobile(brand=brand, model=model, year=year, color=color, license_plate=license_plate, user_id=user_id)  # type: ignore
            session.add(automobile)
            session.flush()  # Flush to get the ID before commit
            # Access attributes to load them into memory before session closes
            _ = automobile.id, automobile.brand, automobile.model, automobile.year, automobile.color, automobile.license_plate, automobile.user_id, automobile.created_at
            # Expunge the object from session to prevent DetachedInstanceError
            session.expunge(automobile)
            # Commit is handled automatically by session_scope
            return automobile
    
    def update_automobile(self, automobile_id: int, brand: Optional[str] = None, model: Optional[str] = None, 
                         year: Optional[int] = None, color: Optional[str] = None, license_plate: Optional[str] = None) -> Optional[Automobile]:
        """Update automobile information"""
        with session_scope() as session:
            automobile = session.query(Automobile).filter(Automobile.id == automobile_id).first()  # type: ignore
            if automobile:
                if brand is not None:
                    automobile.brand = brand
                if model is not None:
                    automobile.model = model
                if year is not None:
                    automobile.year = year
                if color is not None:
                    automobile.color = color
                if license_plate is not None:
                    automobile.license_plate = license_plate
                # Access attributes to load them into memory before session closes
                _ = automobile.id, automobile.brand, automobile.model, automobile.year, automobile.color, automobile.license_plate, automobile.user_id, automobile.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(automobile)
                # Commit is handled automatically by session_scope
            return automobile
    
    def delete_automobile(self, automobile_id: int) -> bool:
        """Delete automobile"""
        with session_scope() as session:
            automobile = session.query(Automobile).filter(Automobile.id == automobile_id).first()  # type: ignore
            if automobile:
                session.delete(automobile)
                # Commit is handled automatically by session_scope
                return True
            return False
    
    # Requirement 4.4: Associate an automobile with a user
    def associate_automobile_to_user(self, automobile_id: int, user_id: int) -> bool:
        """Associate automobile with a user"""
        with session_scope() as session:
            automobile = session.query(Automobile).filter(Automobile.id == automobile_id).first()  # type: ignore
            if automobile:
                automobile.user_id = user_id
                # Commit is handled automatically by session_scope
                return True
            return False
    
    def disassociate_automobile_from_user(self, automobile_id: int) -> bool:
        """Remove automobile association from user"""
        with session_scope() as session:
            automobile = session.query(Automobile).filter(Automobile.id == automobile_id).first()  # type: ignore
            if automobile:
                automobile.user_id = None
                # Commit is handled automatically by session_scope
                return True
            return False
    
    # Requirement 4.6: Get all automobiles
    def get_all_automobiles(self) -> List[Automobile]:
        """Get all automobiles"""
        with session_scope() as session:
            automobiles = session.query(Automobile).all()
            # Access attributes to load them into memory before session closes
            for automobile in automobiles:
                _ = automobile.id, automobile.brand, automobile.model, automobile.year, automobile.color, automobile.license_plate, automobile.user_id, automobile.created_at
                # Expunge each object from session to prevent DetachedInstanceError
                session.expunge(automobile)
            return automobiles
    
    # Utility methods
    def get_automobile(self, automobile_id: int) -> Optional[Automobile]:
        """Get automobile by ID"""
        with session_scope() as session:
            automobile = session.query(Automobile).filter(Automobile.id == automobile_id).first()  # type: ignore
            if automobile:
                # Access attributes to load them into memory before session closes
                _ = automobile.id, automobile.brand, automobile.model, automobile.year, automobile.color, automobile.license_plate, automobile.user_id, automobile.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(automobile)
            return automobile
    
    def get_automobiles_by_user(self, user_id: int) -> List[Automobile]:
        """Get all automobiles for a specific user"""
        with session_scope() as session:
            automobiles = session.query(Automobile).filter(Automobile.user_id == user_id).all()  # type: ignore
            # Access attributes to load them into memory before session closes
            for automobile in automobiles:
                _ = automobile.id, automobile.brand, automobile.model, automobile.year, automobile.color, automobile.license_plate, automobile.user_id, automobile.created_at
                # Expunge each object from session to prevent DetachedInstanceError
                session.expunge(automobile)
            return automobiles
    
    def get_available_automobiles(self) -> List[Automobile]:
        """Get all automobiles that are not associated with any user"""
        with session_scope() as session:
            automobiles = session.query(Automobile).filter(Automobile.user_id == None).all()  # type: ignore
            # Access attributes to load them into memory before session closes
            for automobile in automobiles:
                _ = automobile.id, automobile.brand, automobile.model, automobile.year, automobile.color, automobile.license_plate, automobile.user_id, automobile.created_at
                # Expunge each object from session to prevent DetachedInstanceError
                session.expunge(automobile)
            return automobiles
    
    def get_automobile_by_license_plate(self, license_plate: str) -> Optional[Automobile]:
        """Get automobile by license plate"""
        with session_scope() as session:
            automobile = session.query(Automobile).filter(Automobile.license_plate == license_plate).first()  # type: ignore
            if automobile:
                # Access attributes to load them into memory before session closes
                _ = automobile.id, automobile.brand, automobile.model, automobile.year, automobile.color, automobile.license_plate, automobile.user_id, automobile.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(automobile)
            return automobile 