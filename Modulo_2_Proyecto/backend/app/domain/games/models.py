from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin


if TYPE_CHECKING:
    from app.domain.users.models import User


class GameStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class Game(Base, IntPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "games"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dm_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[GameStatus] = mapped_column(
        SQLEnum(GameStatus, name="game_status"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    # Relationships
    dm_user: Mapped["User"] = relationship("User", back_populates="games")  # type: ignore
    memberships: Mapped[list["GameMembership"]] = relationship(
        "GameMembership", back_populates="game", cascade="all, delete-orphan"
    )
    invites: Mapped[list["GameInvite"]] = relationship(
        "GameInvite", back_populates="game", cascade="all, delete-orphan"
    )


class GameRoleInGame(str, Enum):
    PLAYER = "PLAYER"
    DM = "DM"


class GameMembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    LEFT = "LEFT"
    KICKED = "KICKED"


class GameMembership(Base, IntPrimaryKeyMixin):
    __tablename__ = "game_memberships"
    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_game_memberships_user_id_game_id"),)

    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_in_game: Mapped[GameRoleInGame] = mapped_column(
        SQLEnum(GameRoleInGame, name="game_role_in_game"),
        nullable=False,
    )
    status: Mapped[GameMembershipStatus] = mapped_column(
        SQLEnum(GameMembershipStatus, name="game_membership_status"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="memberships")  # type: ignore
    user: Mapped["User"] = relationship("User", back_populates="game_memberships")  # type: ignore

    # Note:
    # The rule "DM must have a membership with role_in_game=DM" is best enforced in the domain/service layer
    # when creating a game and when transferring DM ownership.


class GameInvite(Base, IntPrimaryKeyMixin):
    __tablename__ = "game_invites"

    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="invites")  # type: ignore
    created_by_user: Mapped["User"] = relationship("User", back_populates="created_game_invites")  # type: ignore

    def is_valid(self) -> bool:
        """
        An invite is valid when:
        - is_active is true
        - game status is ACTIVE
        """
        if not self.is_active:
            return False
        if self.game is None:
            return False
        return self.game.status == GameStatus.ACTIVE