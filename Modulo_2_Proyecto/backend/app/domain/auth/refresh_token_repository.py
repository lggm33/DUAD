from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.auth.models import AuthRefreshToken


class RefreshTokenRepository:
    """Repository for managing refresh token persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self._session = session

    def store(
        self,
        token_hash: str,
        user_id: int,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuthRefreshToken:
        """
        Create and persist a new refresh token.

        Args:
            token_hash: SHA-256 hash of the token
            user_id: ID of the user this token belongs to
            expires_at: When the token expires
            user_agent: Optional user agent string for security tracking
            ip_address: Optional IP address for security tracking

        Returns:
            The created AuthRefreshToken instance
        """
        refresh_token = AuthRefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self._session.add(refresh_token)
        self._session.flush()  # Flush to get the ID without committing

        return refresh_token

    def find_valid(self, token_hash: str) -> Optional[AuthRefreshToken]:
        """
        Find a refresh token by its hash and validate it.

        Args:
            token_hash: The SHA-256 hash of the token to find

        Returns:
            The AuthRefreshToken if found and valid, None otherwise
        """
        token = self._session.query(AuthRefreshToken).filter_by(token_hash=token_hash).first()

        if token is None:
            return None

        # Use the model's is_valid() method to check if not revoked and not expired
        if not token.is_valid():
            return None

        return token

    def revoke(self, token_hash: str) -> bool:
        """
        Mark a refresh token as revoked.

        Args:
            token_hash: The SHA-256 hash of the token to revoke

        Returns:
            True if the token was found and revoked, False otherwise
        """
        token = self._session.query(AuthRefreshToken).filter_by(token_hash=token_hash).first()

        if token is None:
            return False

        # Set revoked_at to current UTC time
        token.revoked_at = datetime.now(timezone.utc)
        self._session.flush()

        return True

    def rotate(
        self,
        old_token_hash: str,
        new_token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[AuthRefreshToken]:
        """
        Revoke an old token and create a new one atomically.

        This operation is transactional - if the old token doesn't exist or
        can't be revoked, the new token won't be created.

        Args:
            old_token_hash: The SHA-256 hash of the token to revoke
            new_token_hash: The SHA-256 hash of the new token
            expires_at: When the new token expires
            user_agent: Optional user agent string for security tracking
            ip_address: Optional IP address for security tracking

        Returns:
            The new AuthRefreshToken if successful, None if old token not found
        """
        # Find the old token
        old_token = self._session.query(AuthRefreshToken).filter_by(token_hash=old_token_hash).first()

        if old_token is None or not old_token.is_valid():
            return None

        # Revoke the old token
        old_token.revoked_at = datetime.now(timezone.utc)

        # Create the new token with the same user_id
        new_token = AuthRefreshToken(
            token_hash=new_token_hash,
            user_id=old_token.user_id,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self._session.add(new_token)
        self._session.flush()

        return new_token
