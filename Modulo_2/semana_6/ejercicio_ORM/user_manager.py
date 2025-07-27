from typing import List, Optional
from database_config import session_scope
from models import User

class UserManager:
    """Class for managing user operations"""
    
    def __init__(self):
        # No longer maintaining a persistent session
        pass
    
    # Requirement 4.1: Create/Update/Delete a new user
    def create_user(self, name: str, email: str, phone: Optional[str] = None) -> User:
        """Create a new user"""
        with session_scope() as session:
            user = User(name=name, email=email, phone=phone)  # type: ignore
            session.add(user)
            session.flush()  # Flush to get the ID before commit
            # Access attributes to load them into memory before session closes
            _ = user.id, user.name, user.email, user.phone, user.created_at
            # Expunge the object from session to prevent DetachedInstanceError
            session.expunge(user)
            # Commit is handled automatically by session_scope
            return user
    
    def update_user(self, user_id: int, name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[User]:
        """Update user information"""
        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()  # type: ignore
            if user:
                if name is not None:
                    user.name = name
                if email is not None:
                    user.email = email
                if phone is not None:
                    user.phone = phone
                # Access attributes to load them into memory before session closes
                _ = user.id, user.name, user.email, user.phone, user.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(user)
                # Commit is handled automatically by session_scope
            return user
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user and all related data"""
        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()  # type: ignore
            if user:
                session.delete(user)
                # Commit is handled automatically by session_scope
                return True
            return False
    
    # Requirement 4.5: Get all users
    def get_all_users(self) -> List[User]:
        """Get all users"""
        with session_scope() as session:
            users = session.query(User).all()
            # Access attributes to load them into memory before session closes
            for user in users:
                _ = user.id, user.name, user.email, user.phone, user.created_at
                # Expunge each object from session to prevent DetachedInstanceError
                session.expunge(user)
            return users
    
    # Utility methods
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()  # type: ignore
            if user:
                # Access attributes to load them into memory before session closes
                _ = user.id, user.name, user.email, user.phone, user.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(user)
            return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        with session_scope() as session:
            user = session.query(User).filter(User.email == email).first()  # type: ignore
            if user:
                # Access attributes to load them into memory before session closes
                _ = user.id, user.name, user.email, user.phone, user.created_at
                # Expunge the object from session to prevent DetachedInstanceError
                session.expunge(user)
            return user 