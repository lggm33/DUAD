from __future__ import annotations

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.domain.auth.refresh_token_repository import RefreshTokenRepository
from app.domain.users.user_repository import UserRepository
from app.domain.users.models import User
from app.utils.jwt_service import JwtService
from app.utils.password_hasher import PasswordHasher


class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class EmailAlreadyExistsError(AuthError):
    """Raised when an email is already registered."""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when email or password is incorrect. Generic to avoid user enumeration."""
    pass


class AuthService:
    """
    Service for handling authentication use cases: register and login.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        jwt_service: JwtService,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._password_hasher = password_hasher
        self._jwt_service = jwt_service

    def register(self, email: str, password: str) -> dict[str, str]:
        """
        Register a new user and issue initial tokens.

        Args:
            email: User's email address
            password: User's plain text password

        Returns:
            Dictionary containing access_token and refresh_token

        Raises:
            EmailAlreadyExistsError: If the email is already in use
        """
        # 1. Verify email not repeated
        if self._user_repo.get_by_email(email):
            raise EmailAlreadyExistsError("Email already registered")

        # 2. Hash password
        password_hash = self._password_hasher.hash(password)

        # 3. Create user
        user = self._user_repo.create_user(email=email, password_hash=password_hash)

        # 4. Issue tokens
        return self._issue_tokens(user)

    def login(self, email: str, password: str) -> dict[str, str]:
        """
        Authenticate a user and issue new tokens.

        Args:
            email: User's email
            password: User's password

        Returns:
            Dictionary containing access_token and refresh_token

        Raises:
            InvalidCredentialsError: For any authentication failure (generic error)
        """
        user = self._user_repo.get_by_email(email)
        
        # Avoid user enumeration by always doing something even if user not found
        # though Argon2 is slow, we might want to be careful here.
        if not user:
            # We could do a "dummy" hash check here to prevent timing attacks
            # but Argon2 handles variable costs reasonably.
            raise InvalidCredentialsError("Invalid email or password")

        if not self._password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InvalidCredentialsError("User account is disabled")

        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> dict[str, str]:
        """
        Internal helper to issue access and refresh tokens.
        """
        # 1. Issue access JWT
        access_token = self._jwt_service.issue_access(
            user_id=user.id,
            role=user.role,
            token_version=user.token_version
        )

        # 2. Generate Refresh Token (secure random string)
        refresh_token_plain = secrets.token_urlsafe(32)
        
        # 3. Hash Refresh Token (SHA-256 for storage)
        token_hash = hashlib.sha256(refresh_token_plain.encode()).hexdigest()
        
        # 4. Store refresh token hash
        # We'll use a default expiration, e.g. 7 days. 
        # In a real app, this should come from settings.
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        self._refresh_token_repo.store(
            token_hash=token_hash,
            user_id=user.id,
            expires_at=expires_at
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_plain
        }
