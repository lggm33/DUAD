from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin


if TYPE_CHECKING:
    from app.domain.users.models import User
    from app.domain.games.ruleset_models import RulesetTemplate
    from app.domain.characters.models import Character
    from app.domain.npcs.models import NPC


class GameStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class CharacterCreationMode(str, Enum):
    """How character creation is handled in this game."""

    OPEN = "OPEN"  # Auto-approved if validation passes
    DM_APPROVAL = "DM_APPROVAL"  # Requires DM approval


class Game(Base, IntPrimaryKeyMixin, TimestampMixin):
    """
    Represents a game session.

    Games can optionally reference a RulesetTemplate for base rules,
    and can have custom_rules that override the template.
    """

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

    # Ruleset configuration
    ruleset_template_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("ruleset_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    custom_rules: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        default=None,
    )
    character_creation_mode: Mapped[CharacterCreationMode] = mapped_column(
        SQLEnum(CharacterCreationMode, name="character_creation_mode"),
        nullable=False,
        server_default=text("'OPEN'"),
    )

    # Turn tracking (volatile state, persisted for reconnection support)
    current_turn_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    current_turn_character_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationships
    dm_user: Mapped["User"] = relationship("User", back_populates="games", foreign_keys=[dm_user_id])
    current_turn_user: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[current_turn_user_id],
        lazy="joined",
    )
    ruleset_template: Mapped["RulesetTemplate | None"] = relationship(
        "RulesetTemplate",
        back_populates="games",
    )
    memberships: Mapped[list["GameMembership"]] = relationship(
        "GameMembership", back_populates="game", cascade="all, delete-orphan"
    )
    invites: Mapped[list["GameInvite"]] = relationship(
        "GameInvite", back_populates="game", cascade="all, delete-orphan"
    )
    characters: Mapped[list["Character"]] = relationship(
        "Character", back_populates="game", cascade="all, delete-orphan"
    )
    npcs: Mapped[list["NPC"]] = relationship(
        "NPC", back_populates="game", cascade="all, delete-orphan"
    )

    def requires_character_approval(self) -> bool:
        """Check if character creation requires DM approval."""
        return self.character_creation_mode == CharacterCreationMode.DM_APPROVAL


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