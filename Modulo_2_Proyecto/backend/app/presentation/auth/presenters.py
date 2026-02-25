from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, TYPE_CHECKING

from app.presentation.base import Presenter

if TYPE_CHECKING:
    from app.domain.users.models import User


class AccessClaimsPresenter(Presenter):
    """
    Presenter for JWT access token claims.
    """

    @staticmethod
    def from_user(user: User) -> dict[str, Any]:
        """
        Build claims for an access token from a user entity.
        
        Args:
            user: The user entity.
            
        Returns:
            Dictionary with JWT claims:
            - sub: user.id
            - role: user.role
            - token_version: user.token_version
            - iat: current timestamp
            - exp: expiration timestamp (15 minutes)
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=15)
        
        return {
            "sub": str(user.id),
            "role": user.role,
            "token_version": user.token_version,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

    @staticmethod
    def public(entity: Any) -> dict[str, Any]:
        """Not implemented for this presenter."""
        raise NotImplementedError("Use from_user() instead")
