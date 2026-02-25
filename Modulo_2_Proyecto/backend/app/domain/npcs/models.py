"""
NPC (Non-Player Character) model.

NPCs are characters controlled by the DM. They can be:
- Created from scratch by the DM
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
    from app.domain.characters.models import Character


class NPCType(str, Enum):
    """Type/role of NPC in the game."""

    ALLY = "ALLY"  # Friendly NPC that helps players
    ENEMY = "ENEMY"  # Hostile NPC (monster, villain)
    NEUTRAL = "NEUTRAL"  # Neutral NPC (merchant, villager)
    BOSS = "BOSS"  # Major enemy/boss
    COMPANION = "COMPANION"  # Travels with party


class NPCStatus(str, Enum):
    """Current status of the NPC."""

    ACTIVE = "ACTIVE"  # Available for encounters
    DEFEATED = "DEFEATED"  # Defeated in combat
    RETIRED = "RETIRED"  # No longer in game


class NPC(Base, IntPrimaryKeyMixin, TimestampMixin):
    """
    Non-Player Character model.

    NPCs belong to a game and are controlled by the DM.
    They can participate in encounters and have combat stats.
    """

    __tablename__ = "npcs"

    game_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    npc_type: Mapped[NPCType] = mapped_column(
        SQLEnum(NPCType, name="npc_type"),
        nullable=False,
        server_default=text("'NEUTRAL'"),
    )
    status: Mapped[NPCStatus] = mapped_column(
        SQLEnum(NPCStatus, name="npc_status"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Combat stats stored as JSON for flexibility
    stats: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Full character data (same structure as Character.data)
    data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Relationships
    game: Mapped["Game"] = relationship(
        "Game",
        back_populates="npcs",
        foreign_keys=[game_id]
    )

