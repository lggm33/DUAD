from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin


class AuthRefreshToken(Base, IntPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "auth_refresh_tokens"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")  # type: ignore

    def is_revoked(self) -> bool:
        """Check if the refresh token has been revoked."""
        return self.revoked_at is not None

    def is_expired(self) -> bool:
        """Check if the refresh token has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid(self) -> bool:
        """Check if the refresh token is valid (not revoked and not expired)."""
        return not self.is_revoked() and not self.is_expired()


@dataclass(frozen=True)
class AuthUser:
    """
    Object representing the authenticated user in the current request context.
    """
    user_id: int
    role: str
