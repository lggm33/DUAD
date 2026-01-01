"""
Encounter models for combat management.

Includes:
- Encounter: Groups participants for a combat scenario
- EncounterParticipant: Links characters/NPCs to encounters
- EncounterState: Real-time combat state (initiative, HP, conditions)
- CombatLog: Persistent log of all combat actions
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.common.models import Base, IntPrimaryKeyMixin, TimestampMixin


if TYPE_CHECKING:
    from app.domain.games.models import Game
    from app.domain.users.models import User


# =============================================================================
# Enums
# =============================================================================


class EncounterStatus(str, Enum):
    """Status of an encounter."""

    DRAFT = "DRAFT"  # Being prepared
    READY = "READY"  # Ready to start
    ACTIVE = "ACTIVE"  # Combat in progress
    PAUSED = "PAUSED"  # Temporarily paused
    COMPLETED = "COMPLETED"  # Finished


class EncounterDifficulty(str, Enum):
    """Difficulty rating for the encounter."""

    TRIVIAL = "TRIVIAL"
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    DEADLY = "DEADLY"


class EncounterOutcome(str, Enum):
    """Outcome of a completed encounter."""

    VICTORY = "VICTORY"  # Players won
    DEFEAT = "DEFEAT"  # Players lost
    FLED = "FLED"  # Players fled
    NEGOTIATED = "NEGOTIATED"  # Resolved without combat
    ABORTED = "ABORTED"  # DM ended prematurely


class ParticipantType(str, Enum):
    """Type of encounter participant."""

    CHARACTER = "CHARACTER"  # Player character
    NPC = "NPC"  # Non-player character


class EncounterStateStatus(str, Enum):
    """Status of combat state."""

    ROLLING_INITIATIVE = "ROLLING_INITIATIVE"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_RECONNECT = "WAITING_RECONNECT"
    PAUSED = "PAUSED"
    ENDED = "ENDED"


class CombatActionType(str, Enum):
    """Types of combat actions for logging."""

    INITIATIVE_ROLL = "INITIATIVE_ROLL"
    ATTACK = "ATTACK"
    DAMAGE = "DAMAGE"
    HEAL = "HEAL"
    SPELL = "SPELL"
    ABILITY = "ABILITY"
    MOVEMENT = "MOVEMENT"
    CONDITION_APPLY = "CONDITION_APPLY"
    CONDITION_REMOVE = "CONDITION_REMOVE"
    DEATH = "DEATH"
    TURN_START = "TURN_START"
    TURN_END = "TURN_END"
    TURN_SKIPPED = "TURN_SKIPPED"
    DM_OVERRIDE = "DM_OVERRIDE"
    CUSTOM = "CUSTOM"


class ActorType(str, Enum):
    """Type of actor performing an action."""

    CHARACTER = "CHARACTER"
    NPC = "NPC"
    SYSTEM = "SYSTEM"


# =============================================================================
# Models
# =============================================================================


class Encounter(Base, IntPrimaryKeyMixin, TimestampMixin):
    """
    Represents a combat encounter in a game.

    Groups participants (characters and NPCs) for a combat scenario.
    """

    __tablename__ = "encounters"

    game_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[EncounterStatus] = mapped_column(
        SQLEnum(EncounterStatus, name="encounter_status"),
        nullable=False,
        server_default=text("'DRAFT'"),
    )
    difficulty: Mapped[EncounterDifficulty | None] = mapped_column(
        SQLEnum(EncounterDifficulty, name="encounter_difficulty"),
        nullable=True,
    )
    estimated_xp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcome: Mapped[EncounterOutcome | None] = mapped_column(
        SQLEnum(EncounterOutcome, name="encounter_outcome"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="encounters")
    participants: Mapped[list["EncounterParticipant"]] = relationship(
        "EncounterParticipant",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )
    state: Mapped["EncounterState | None"] = relationship(
        "EncounterState",
        back_populates="encounter",
        uselist=False,
        cascade="all, delete-orphan",
    )
    combat_logs: Mapped[list["CombatLog"]] = relationship(
        "CombatLog",
        back_populates="encounter",
        cascade="all, delete-orphan",
    )


class EncounterParticipant(Base, IntPrimaryKeyMixin):
    """
    Links a character or NPC to an encounter.

    Supports multiple instances of the same NPC (e.g., "Goblin 1", "Goblin 2").
    """

    __tablename__ = "encounter_participants"

    encounter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encounters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    participant_type: Mapped[ParticipantType] = mapped_column(
        SQLEnum(ParticipantType, name="participant_type"),
        nullable=False,
    )
    participant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    instance_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    encounter: Mapped["Encounter"] = relationship(
        "Encounter",
        back_populates="participants",
    )


class EncounterState(Base, IntPrimaryKeyMixin):
    """
    Real-time state of an active combat encounter.

    Tracks initiative order, current turn, HP, conditions, and connection status.
    One-to-one relationship with Encounter.
    """

    __tablename__ = "encounter_states"

    encounter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encounters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    current_round: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )
    current_turn_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    initiative_order: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    combatants_state: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    turn_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[EncounterStateStatus] = mapped_column(
        SQLEnum(EncounterStateStatus, name="encounter_state_status"),
        nullable=False,
        server_default=text("'ROLLING_INITIATIVE'"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    encounter: Mapped["Encounter"] = relationship(
        "Encounter",
        back_populates="state",
    )


class CombatLog(Base, IntPrimaryKeyMixin):
    """
    Persistent log of all combat actions.

    Records every action taken during an encounter for history,
    replay, and debugging.
    """

    __tablename__ = "combat_logs"

    encounter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("encounters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    action_type: Mapped[CombatActionType] = mapped_column(
        SQLEnum(CombatActionType, name="combat_action_type"),
        nullable=False,
    )
    actor_type: Mapped[ActorType] = mapped_column(
        SQLEnum(ActorType, name="actor_type"),
        nullable=False,
    )
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_type: Mapped[ActorType | None] = mapped_column(
        SQLEnum(ActorType, name="actor_type", create_constraint=False),
        nullable=True,
    )
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    encounter: Mapped["Encounter"] = relationship(
        "Encounter",
        back_populates="combat_logs",
    )
    created_by_user: Mapped["User | None"] = relationship("User")

