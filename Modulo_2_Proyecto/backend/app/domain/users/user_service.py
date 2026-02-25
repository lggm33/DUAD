from __future__ import annotations

from typing import Optional

from app.domain.users.user_repository import UserRepository
from app.domain.users.models import User


class UserService:
    """
    Service for handling user-related business logic.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by their ID.

        Args:
            user_id: The ID of the user to retrieve.

        Returns:
            The User instance if found, None otherwise.
        """
        return self._user_repo.get_by_id(user_id)

    def update_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update a user's profile with validation.

        Args:
            user_id: ID of the user to update
            name: New name (optional)
            username: New username (optional)
            email: New email (optional)

        Returns:
            The updated User instance or None if user not found

        Raises:
            ValueError: If email or username is already taken by another user
        """
        user = self._user_repo.get_by_id(user_id)
        if not user:
            return None

        if email and email != user.email:
            if self._user_repo.get_by_email(email):
                raise ValueError("Email already in use")

        if username and username != user.username:
            if self._user_repo.get_by_username(username):
                raise ValueError("Username already in use")

        return self._user_repo.update_user(
            user, name=name, username=username, email=email
        )
