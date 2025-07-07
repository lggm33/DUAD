from typing import List, Optional
from database_config import get_session
from models import Automobile

class AutomobileManager:
    """Class for managing automobile operations"""
    
    def __init__(self):
        self.session = get_session()
    
    # Requirement 4.2: Create/Update/Delete a new automobile
    def create_automobile(self, brand: str, model: str, year: int, color: str, 
                         license_plate: str, user_id: Optional[int] = None) -> Automobile:
        """Create a new automobile"""
        automobile = Automobile(brand=brand, model=model, year=year, color=color, license_plate=license_plate, user_id=user_id)  # type: ignore
        self.session.add(automobile)
        self.session.commit()
        return automobile
    
    def update_automobile(self, automobile_id: int, brand: Optional[str] = None, model: Optional[str] = None, 
                         year: Optional[int] = None, color: Optional[str] = None, license_plate: Optional[str] = None) -> Optional[Automobile]:
        """Update automobile information"""
        automobile = self.get_automobile(automobile_id)
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
            self.session.commit()
        return automobile
    
    def delete_automobile(self, automobile_id: int) -> bool:
        """Delete automobile"""
        automobile = self.get_automobile(automobile_id)
        if automobile:
            self.session.delete(automobile)
            self.session.commit()
            return True
        return False
    
    # Requirement 4.4: Associate an automobile with a user
    def associate_automobile_to_user(self, automobile_id: int, user_id: int) -> bool:
        """Associate automobile with a user"""
        automobile = self.get_automobile(automobile_id)
        if automobile:
            automobile.user_id = user_id
            self.session.commit()
            return True
        return False
    
    def disassociate_automobile_from_user(self, automobile_id: int) -> bool:
        """Remove automobile association from user"""
        automobile = self.get_automobile(automobile_id)
        if automobile:
            automobile.user_id = None
            self.session.commit()
            return True
        return False
    
    # Requirement 4.6: Get all automobiles
    def get_all_automobiles(self) -> List[Automobile]:
        """Get all automobiles"""
        return self.session.query(Automobile).all()
    
    # Utility methods
    def get_automobile(self, automobile_id: int) -> Optional[Automobile]:
        """Get automobile by ID"""
        return self.session.query(Automobile).filter(Automobile.id == automobile_id).first()  # type: ignore
    
    def get_automobiles_by_user(self, user_id: int) -> List[Automobile]:
        """Get all automobiles for a specific user"""
        return self.session.query(Automobile).filter(Automobile.user_id == user_id).all()  # type: ignore
    
    def get_available_automobiles(self) -> List[Automobile]:
        """Get all automobiles that are not associated with any user"""
        return self.session.query(Automobile).filter(Automobile.user_id == None).all()  # type: ignore
    
    def get_automobile_by_license_plate(self, license_plate: str) -> Optional[Automobile]:
        """Get automobile by license plate"""
        return self.session.query(Automobile).filter(Automobile.license_plate == license_plate).first()  # type: ignore
    
    def close_session(self):
        """Close the database session"""
        self.session.close()
    
    def __del__(self):
        self.session.close() 