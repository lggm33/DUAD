from typing import List, Optional
from database_config import get_session
from models import Address

class AddressManager:
    """Class for managing address operations"""
    
    def __init__(self):
        self.session = get_session()
    
    # Requirement 4.3: Create/Update/Delete a new address
    def create_address(self, street: str, city: str, state: str, zip_code: str, user_id: int) -> Address:
        """Create a new address"""
        address = Address(street=street, city=city, state=state, zip_code=zip_code, user_id=user_id)  # type: ignore
        self.session.add(address)
        self.session.commit()
        return address
    
    def update_address(self, address_id: int, street: Optional[str] = None, city: Optional[str] = None, 
                      state: Optional[str] = None, zip_code: Optional[str] = None) -> Optional[Address]:
        """Update address information"""
        address = self.get_address(address_id)
        if address:
            if street is not None:
                address.street = street
            if city is not None:
                address.city = city
            if state is not None:
                address.state = state
            if zip_code is not None:
                address.zip_code = zip_code
            self.session.commit()
        return address
    
    def delete_address(self, address_id: int) -> bool:
        """Delete address"""
        address = self.get_address(address_id)
        if address:
            self.session.delete(address)
            self.session.commit()
            return True
        return False
    
        # Requirement 4.7: Get all addresses
    def get_all_addresses(self) -> List[Address]:
        """Get all addresses"""
        return self.session.query(Address).all()
    
    # Utility methods
    def get_address(self, address_id: int) -> Optional[Address]:
        """Get address by ID"""
        return self.session.query(Address).filter(Address.id == address_id).first()  # type: ignore
    
    def get_addresses_by_user(self, user_id: int) -> List[Address]:
        """Get all addresses for a specific user"""
        return self.session.query(Address).filter(Address.user_id == user_id).all()  # type: ignore
    
    def close_session(self):
        """Close the database session"""
        self.session.close()
    
    def __del__(self):
        self.session.close() 