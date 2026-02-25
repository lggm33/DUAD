"""
JWT Service for issuing and verifying JSON Web Tokens.

This module provides utilities for creating and validating JWT access tokens
used for authentication.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


class JwtError(Exception):
    """Base exception for JWT errors."""
    pass


class JwtExpiredError(JwtError):
    """Raised when JWT has expired."""
    pass


class JwtInvalidError(JwtError):
    """Raised when JWT is invalid or tampered."""
    pass


class JwtService:
    """
    Service for issuing and verifying JWT access tokens.
    
    This service handles the creation and validation of JWT tokens used
    for authentication. Tokens include claims for user identification,
    role-based access control, and token versioning.
    
    Example:
        >>> service = JwtService(secret_key="my-secret", algorithm="HS256")
        >>> token = service.issue_access(user_id=123, role="USER", token_version=1)
        >>> claims = service.verify(token)
        >>> claims["sub"]
        '123'
    """

    def __init__(
        self, 
        secret_key: str, 
        algorithm: str = "HS256",
        access_token_expires: int = 3600
    ) -> None:
        """
        Initialize the JwtService.

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm to use (default: HS256)
            access_token_expires: Token expiration in seconds (default: 3600 = 1 hour)
        
        Raises:
            ValueError: If secret_key is empty
        """
        if not secret_key or not secret_key.strip():
            raise ValueError("Secret key cannot be empty")
        
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_token_expires = access_token_expires

    def issue_access(
        self, 
        user_id: int, 
        role: str, 
        token_version: int
    ) -> str:
        """
        Issue a new JWT access token.
        
        Note: This is deprecated in favor of using AccessClaimsPresenter 
              and encode_payload().

        Args:
            user_id: The user's ID
            role: The user's role (e.g., "USER", "ADMIN")
            token_version: The user's token version for invalidation

        Returns:
            A signed JWT token string

        Raises:
            ValueError: If inputs are invalid
        """
        if user_id <= 0:
            raise ValueError("User ID must be positive")
        
        if not role or not role.strip():
            raise ValueError("Role cannot be empty")
        
        if token_version < 1:
            raise ValueError("Token version must be at least 1")
        
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self._access_token_expires)
        
        payload: dict[str, Any] = {
            "sub": str(user_id),  # Subject: user ID as string
            "role": role.strip(),
            "token_version": token_version,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expires_at.timestamp()),  # Expires at
        }
        
        return self.encode_payload(payload)

    def encode_payload(self, payload: dict[str, Any]) -> str:
        """
        Encode a dictionary payload into a signed JWT token.

        Args:
            payload: Dictionary containing token claims

        Returns:
            A signed JWT token string
        """
        token = jwt.encode(
            payload, 
            self._secret_key, 
            algorithm=self._algorithm
        )
        return token

    def verify(self, token: str) -> dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: The JWT token string to verify

        Returns:
            Dictionary containing the token claims

        Raises:
            JwtExpiredError: If the token has expired
            JwtInvalidError: If the token is invalid or tampered

        Example:
            >>> service = JwtService("secret")
            >>> token = service.issue_access(123, "USER", 1)
            >>> claims = service.verify(token)
            >>> claims["role"]
            'USER'
        """
        if not token or not token.strip():
            raise JwtInvalidError("Token cannot be empty")
        
        try:
            payload = jwt.decode(
                token.strip(),
                self._secret_key,
                algorithms=[self._algorithm]
            )
            return payload
        
        except ExpiredSignatureError:
            raise JwtExpiredError("Token has expired")
        
        except InvalidTokenError as e:
            raise JwtInvalidError(f"Invalid token: {str(e)}")
