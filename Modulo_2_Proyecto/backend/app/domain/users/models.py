from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domain.auth.models import AuthRefreshToken


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base, IntPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)

    # Global RBAC role (ADMIN/USER). Default is USER.
    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'USER'"))
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    # Relationships
    refresh_tokens: Mapped[list["AuthRefreshToken"]] = relationship(
        "AuthRefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
