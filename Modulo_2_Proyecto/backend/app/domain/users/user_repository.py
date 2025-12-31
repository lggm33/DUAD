from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.users.models import User, UserRole


class UserRepository:
    """Repository for managing user persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self._session = session

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Find a user by their email address.

        Args:
            email: The email address to search for

        Returns:
            The User if found, None otherwise
        """
        return self._session.query(User).filter_by(email=email).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Find a user by their username.

        Args:
            username: The username to search for

        Returns:
            The User if found, None otherwise
        """
        return self._session.query(User).filter_by(username=username).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Find a user by their ID.

        Args:
            user_id: The ID of the user to find

        Returns:
            The User if found, None otherwise
        """
        return self._session.get(User, user_id)

    def get_users_by_ids(self, user_ids: list[int]) -> list[User]:
        """
        Find users by a list of IDs.

        Args:
            user_ids: List of user IDs to find

        Returns:
            List of Users found
        """
        if not user_ids:
            return []
        return self._session.query(User).filter(User.id.in_(user_ids)).all()

    def create_user(
        self,
        email: str,
        password_hash: str,
        name: str,
        username: Optional[str] = None,
        role: str = UserRole.USER.value,
        is_active: bool = True,
    ) -> User:
        """
        Create a new user with a hashed password.

        Note: This method expects a pre-hashed password. Password hashing
        should be done in the service layer before calling this method.

        Args:
            email: User's email address (must be unique)
            password_hash: Pre-hashed password (e.g., bcrypt hash)
            name: User's full name
            username: User's chosen username (optional, unique)
            role: User role (default: "USER")
            is_active: Whether the account is active (default: True)

        Returns:
            The created User instance
        """
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            username=username,
            role=role,
            is_active=is_active,
        )

        self._session.add(user)
        self._session.flush()  # Get the ID without committing

        return user
