from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.domain.auth.models import AuthRefreshToken
    from app.domain.games.models import Game
    from app.domain.games.models import GameInvite, GameMembership
    from app.domain.games.ruleset_models import RulesetTemplate
    from app.domain.characters.models import Character


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

    games: Mapped[list["Game"]] = relationship("Game", back_populates="dm_user")
    game_memberships: Mapped[list["GameMembership"]] = relationship(
        "GameMembership", back_populates="user", cascade="all, delete-orphan"
    )
    created_game_invites: Mapped[list["GameInvite"]] = relationship(
        "GameInvite", back_populates="created_by_user", cascade="all, delete-orphan"
    )
    created_ruleset_templates: Mapped[list["RulesetTemplate"]] = relationship(
        "RulesetTemplate", back_populates="created_by_user"
    )
    characters: Mapped[list["Character"]] = relationship(
        "Character", back_populates="user", cascade="all, delete-orphan"
    )
