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
