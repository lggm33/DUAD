import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.domain.auth.auth_service import (
    AuthService, 
    EmailAlreadyExistsError, 
    InvalidCredentialsError,
    TokenInvalidError
)
from app.domain.users.models import User
from app.domain.users.user_repository import UserRepository
from app.domain.auth.refresh_token_repository import RefreshTokenRepository
from app.utils.password_hasher import PasswordHasher
from app.utils.jwt_service import JwtService


@pytest.fixture
def mock_user_repo():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_refresh_repo():
    return MagicMock(spec=RefreshTokenRepository)


@pytest.fixture
def mock_hasher():
    return MagicMock(spec=PasswordHasher)


@pytest.fixture
def mock_jwt_service():
    return MagicMock(spec=JwtService)


@pytest.fixture
def auth_service(mock_user_repo, mock_refresh_repo, mock_hasher, mock_jwt_service):
    return AuthService(
        user_repo=mock_user_repo,
        refresh_token_repo=mock_refresh_repo,
        password_hasher=mock_hasher,
        jwt_service=mock_jwt_service
    )


def test_register_success(auth_service, mock_user_repo, mock_hasher, mock_jwt_service, mock_refresh_repo):
    # Setup
    email = "test@example.com"
    password = "password123"
    hashed_password = "hashed_password"
    
    mock_user_repo.get_by_email.return_value = None
    mock_hasher.hash.return_value = hashed_password
    
    user = User(id=1, email=email, password_hash=hashed_password, role="USER", token_version=1)
    mock_user_repo.create_user.return_value = user
    
    mock_jwt_service.encode_payload.return_value = "access_token"
    
    # Execute
    result = auth_service.register(email=email, password=password, name="Test User")
    
    # Assert
    assert result["access_token"] == "access_token"
    assert "refresh_token" in result
    mock_user_repo.get_by_email.assert_called_once_with(email)
    mock_hasher.hash.assert_called_once_with(password)
    mock_user_repo.create_user.assert_called_once_with(
        email=email, 
        password_hash=hashed_password,
        name="Test User",
        username=None
    )
    mock_refresh_repo.store.assert_called_once()


def test_register_duplicate_email(auth_service, mock_user_repo):
    # Setup
    email = "existing@example.com"
    mock_user_repo.get_by_email.return_value = User(id=1, email=email)
    
    # Execute & Assert
    with pytest.raises(EmailAlreadyExistsError):
        auth_service.register(email=email, password="password", name="Test User")


def test_login_success(auth_service, mock_user_repo, mock_hasher, mock_jwt_service):
    # Setup
    email = "test@example.com"
    password = "password123"
    user = User(id=1, email=email, password_hash="hashed", role="USER", token_version=1, is_active=True)
    
    mock_user_repo.get_by_email.return_value = user
    mock_hasher.verify.return_value = True
    mock_jwt_service.encode_payload.return_value = "access_token"
    
    # Execute
    result = auth_service.login(email, password)
    
    # Assert
    assert result["access_token"] == "access_token"
    assert "refresh_token" in result
    mock_hasher.verify.assert_called_once_with(password, "hashed")


def test_login_invalid_password(auth_service, mock_user_repo, mock_hasher):
    # Setup
    email = "test@example.com"
    user = User(id=1, email=email, password_hash="hashed", is_active=True)
    
    mock_user_repo.get_by_email.return_value = user
    mock_hasher.verify.return_value = False
    
    # Execute & Assert
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(email, "wrong_password")


def test_login_user_not_found(auth_service, mock_user_repo):
    # Setup
    mock_user_repo.get_by_email.return_value = None
    
    # Execute & Assert
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("nonexistent@example.com", "password")


def test_login_inactive_user(auth_service, mock_user_repo, mock_hasher):
    # Setup
    user = User(id=1, email="test@example.com", password_hash="hashed", is_active=False)
    mock_user_repo.get_by_email.return_value = user
    mock_hasher.verify.return_value = True
    
    # Execute & Assert
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("test@example.com", "password")


def test_refresh_success(auth_service, mock_refresh_repo, mock_jwt_service):
    # Setup
    old_token = "old_token"
    new_token_plain = "new_token"
    user = User(id=1, role="USER", token_version=1)
    new_rt = MagicMock()
    new_rt.user = user
    
    mock_refresh_repo.rotate.return_value = new_rt
    mock_jwt_service.encode_payload.return_value = "new_access_token"
    
    # Execute
    # We can't easily mock the random token generation inside the method to match
    # but we can check if it returns what the mock says or similar.
    # Actually, new_token_plain is generated inside.
    result = auth_service.refresh(old_token)
    
    # Assert
    assert result["access_token"] == "new_access_token"
    assert "refresh_token" in result
    mock_refresh_repo.rotate.assert_called_once()


def test_refresh_invalid_token(auth_service, mock_refresh_repo):
    # Setup
    mock_refresh_repo.rotate.return_value = None
    
    # Execute & Assert
    with pytest.raises(TokenInvalidError):
        auth_service.refresh("invalid_token")


def test_logout_success(auth_service, mock_refresh_repo):
    # Setup
    token = "token_to_logout"
    
    # Execute
    auth_service.logout(token)
    
    # Assert
    mock_refresh_repo.revoke.assert_called_once()
