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

    def create_user(
        self,
        email: str,
        password_hash: str,
        name: str,
        username: Optional[str] = None,
        role: UserRole = UserRole.USER,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User's email address
            password_hash: Hashed password
            name: User's full name
            username: User's username (optional)
            role: User's role (defaults to PLAYER)

        Returns:
            The newly created User instance
        """
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            username=username,
            role=role,
        )
        self._session.add(user)
        self._session.flush()
        return user

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

    def get_all_users(self) -> list[User]:
        """
        Get all users.
        """
        return self._session.query(User).order_by(User.name.asc()).all()

    def update_user(
        self,
        user: User,
        name: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
    ) -> User:
        """
        Update an existing user's profile information.

        Args:
            user: The User instance to update
            name: New full name (optional)
            username: New username (optional)
            email: New email address (optional)

        Returns:
            The updated User instance
        """
        if name is not None:
            user.name = name
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email

        self._session.flush()
        return user
