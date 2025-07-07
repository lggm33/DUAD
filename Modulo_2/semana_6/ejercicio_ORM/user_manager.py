from typing import List, Optional
from database_config import get_session
from models import User

class UserManager:
    """Class for managing user operations"""
    
    def __init__(self):
        self.session = get_session()
    
    # Requirement 4.1: Create/Update/Delete a new user
    def create_user(self, name: str, email: str, phone: Optional[str] = None) -> User:
        """Create a new user"""
        user = User(name=name, email=email, phone=phone)  # type: ignore
        self.session.add(user)
        self.session.commit()
        return user
    
    def update_user(self, user_id: int, name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[User]:
        """Update user information"""
        user = self.get_user(user_id)
        if user:
            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            if phone is not None:
                user.phone = phone
            self.session.commit()
        return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user and all related data"""
        user = self.get_user(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
    
    # Requirement 4.5: Get all users
    def get_all_users(self) -> List[User]:
        """Get all users"""
        return self.session.query(User).all()
    
    # Utility methods
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.session.query(User).filter(User.id == user_id).first()  # type: ignore
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.session.query(User).filter(User.email == email).first()  # type: ignore
    
    def close_session(self):
        """Close the database session"""
        self.session.close()
    
    def __del__(self):
        self.session.close() 