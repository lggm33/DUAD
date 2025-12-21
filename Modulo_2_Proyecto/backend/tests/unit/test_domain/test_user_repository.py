import pytest
from app.domain.users.user_repository import UserRepository
from app.domain.users.models import User, UserRole

def test_get_by_id_returns_user_if_exists(session):
    # Arrange
    user_repo = UserRepository(session)
    user = user_repo.create_user(
        email="test_repo@example.com",
        password_hash="hash",
        name="Test User"
    )
    # No commit needed for same-session fetch

    # Act
    found_user = user_repo.get_by_id(user.id)

    # Assert
    assert found_user is not None
    assert found_user.id == user.id
    assert found_user.email == "test_repo@example.com"

def test_get_by_id_returns_none_if_not_exists(session):
    # Arrange
    user_repo = UserRepository(session)

    # Act
    found_user = user_repo.get_by_id(9999)

    # Assert
    assert found_user is None
