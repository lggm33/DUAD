"""
Character model for player characters (PCs).

Represents characters created by players for a specific game,
following the game's ruleset and requiring optional DM approval.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text, text
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin


if TYPE_CHECKING:
    from app.domain.games.models import Game
    from app.domain.users.models import User


class CharacterStatus(str, Enum):
    """Status of a character in the approval workflow."""

    DRAFT = "DRAFT"  # Still being created/edited by player
    PENDING_APPROVAL = "PENDING_APPROVAL"  # Submitted for DM review
    APPROVED = "APPROVED"  # Approved by DM, ready to play
    REJECTED = "REJECTED"  # Rejected by DM, needs changes
    CONVERTED_TO_NPC = "CONVERTED_TO_NPC"  # Player left, character is now NPC


class Character(Base, IntPrimaryKeyMixin, TimestampMixin):
    """
    Player Character (PC) model.

    Characters belong to a game and a user. They store character data
    as JSON and go through an approval workflow if the game requires it.
    """

    __tablename__ = "characters"

    game_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CharacterStatus] = mapped_column(
        SQLEnum(CharacterStatus, name="character_status"),
        nullable=False,
        server_default=text("'DRAFT'"),
    )
    data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    dm_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    converted_to_npc_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("npcs.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="characters")
    user: Mapped["User"] = relationship("User", back_populates="characters")

    def is_editable(self) -> bool:
        """Check if character can be edited by the player."""
        return self.status in (CharacterStatus.DRAFT, CharacterStatus.REJECTED)

    def is_playable(self) -> bool:
        """Check if character is approved and can be used in game."""
        return self.status == CharacterStatus.APPROVED

