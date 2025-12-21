from typing import Any
from app.presentation.base import Presenter
from app.domain.users.models import User

class UserPresenter(Presenter):
    """
    Presenter for User entities.
    """
    
    @staticmethod
    def public(user: User) -> dict[str, Any]:
        """
        Returns a public dictionary for a User.
        """
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "username": user.username,
            "role": user.role
        }

    @staticmethod
    def collection(users: list[User]) -> list[dict[str, Any]]:
        """
        Returns a list of public dictionaries for a collection of Users.
        """
        return [UserPresenter.public(user) for user in users]
