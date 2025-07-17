from typing import List, Optional
from database_config import session_scope
from models import Address

class AddressManager:
    """Class for managing address operations"""
    
    def __init__(self):
        # No longer maintaining a persistent session
        pass
    
    # Requirement 4.3: Create/Update/Delete a new address
    def create_address(self, street: str, city: str, state: str, zip_code: str, user_id: int) -> Address:
        """Create a new address"""
        with session_scope() as session:
            address = Address(street=street, city=city, state=state, zip_code=zip_code, user_id=user_id)  # type: ignore
            session.add(address)
            session.flush()  # Flush to get the ID before commit
            # Access attributes to load them into memory before session closes
            _ = address.id, address.street, address.city, address.state, address.zip_code, address.user_id, address.created_at
            # Expunge the object from session to prevent DetachedInstanceError
            session.expunge(address)
            # Commit is handled automatically by session_scope
            return address
    
    def update_address(self, address_id: int, street: Optional[str] = None, city: Optional[str] = None, 
                      state: Optional[str] = None, zip_code: Optional[str] = None) -> Optional[Address]:
        """Update address information"""
        with session_scope() as session:
            address = session.query(Address).filter(Address.id == address_id).first()  # type: ignore
            if address:
                if street is not None:
                    address.street = street
                if city is not None:
                    address.city = city
                if state is not None:
                    address.state = state
                if zip_code is not None:
                    address.zip_code = zip_code
                # Access attributes to load them into memory before session closes
                _ = address.id, address.street, address.city, address.state, address.zip_code, address.user_id, address.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(address)
                # Commit is handled automatically by session_scope
            return address
    
    def delete_address(self, address_id: int) -> bool:
        """Delete address"""
        with session_scope() as session:
            address = session.query(Address).filter(Address.id == address_id).first()  # type: ignore
            if address:
                session.delete(address)
                # Commit is handled automatically by session_scope
                return True
            return False
    
        # Requirement 4.7: Get all addresses
    def get_all_addresses(self) -> List[Address]:
        """Get all addresses"""
        with session_scope() as session:
            addresses = session.query(Address).all()
            # Access attributes to load them into memory before session closes
            for address in addresses:
                _ = address.id, address.street, address.city, address.state, address.zip_code, address.user_id, address.created_at
                # Expunge each object from session to prevent DetachedInstanceError
                session.expunge(address)
            return addresses
    
    # Utility methods
    def get_address(self, address_id: int) -> Optional[Address]:
        """Get address by ID"""
        with session_scope() as session:
            address = session.query(Address).filter(Address.id == address_id).first()  # type: ignore
            if address:
                # Access attributes to load them into memory before session closes
                _ = address.id, address.street, address.city, address.state, address.zip_code, address.user_id, address.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(address)
            return address
    
    def get_addresses_by_user(self, user_id: int) -> List[Address]:
        """Get all addresses for a specific user"""
        with session_scope() as session:
            addresses = session.query(Address).filter(Address.user_id == user_id).all()  # type: ignore
            # Access attributes to load them into memory before session closes
            for address in addresses:
                _ = address.id, address.street, address.city, address.state, address.zip_code, address.user_id, address.created_at
                # Expunge each object from session to prevent DetachedInstanceError
                session.expunge(address)
            return addresses 