"""
Repository for Encounter persistence operations.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.domain.encounters.models import (
    Encounter,
    EncounterParticipant,
    EncounterState,
    EncounterStatus,
    CombatLog,
)


class EncounterRepository:
    """Repository for managing encounter persistence."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # =========================================================================
    # Encounter CRUD
    # =========================================================================

    def create(self, encounter: Encounter) -> Encounter:
        """Create a new encounter."""
        self._session.add(encounter)
        self._session.flush()
        return encounter

    def get_by_id(self, encounter_id: int) -> Optional[Encounter]:
        """Get an encounter by ID with all relationships."""
        return (
            self._session.query(Encounter)
            .options(
                joinedload(Encounter.participants),
                joinedload(Encounter.state),
            )
            .filter_by(id=encounter_id)
            .first()
        )

    def get_by_game_id(self, game_id: int) -> list[Encounter]:
        """Get all encounters in a game."""
        return self._session.query(Encounter).filter_by(game_id=game_id).all()

    def get_active_by_game_id(self, game_id: int) -> list[Encounter]:
        """Get active encounters in a game."""
        return (
            self._session.query(Encounter)
            .filter_by(game_id=game_id, status=EncounterStatus.ACTIVE)
            .all()
        )

    def get_by_status(
        self,
        game_id: int,
        status: EncounterStatus,
    ) -> list[Encounter]:
        """Get encounters by status."""
        return (
            self._session.query(Encounter)
            .filter_by(game_id=game_id, status=status)
            .all()
        )

    def delete(self, encounter: Encounter) -> None:
        """Delete an encounter."""
        self._session.delete(encounter)
        self._session.flush()

    # =========================================================================
    # Participant operations
    # =========================================================================

    def add_participant(
        self,
        participant: EncounterParticipant,
    ) -> EncounterParticipant:
        """Add a participant to an encounter."""
        self._session.add(participant)
        self._session.flush()
        return participant

    def get_participants(self, encounter_id: int) -> list[EncounterParticipant]:
        """Get all participants in an encounter."""
        return (
            self._session.query(EncounterParticipant)
            .filter_by(encounter_id=encounter_id)
            .all()
        )

    def get_participant_by_id(
        self,
        participant_id: int,
    ) -> Optional[EncounterParticipant]:
        """Get a participant by ID."""
        return (
            self._session.query(EncounterParticipant)
            .filter_by(id=participant_id)
            .first()
        )

    def remove_participant(self, participant: EncounterParticipant) -> None:
        """Remove a participant from an encounter."""
        self._session.delete(participant)
        self._session.flush()

    def remove_participant_by_id(self, participant_id: int) -> bool:
        """Remove a participant by ID. Returns True if deleted, False if not found."""
        participant = self.get_participant_by_id(participant_id)
        if not participant:
            return False
        self._session.delete(participant)
        self._session.flush()
        return True

    # =========================================================================
    # State operations
    # =========================================================================

    def create_state(self, state: EncounterState) -> EncounterState:
        """Create encounter state."""
        self._session.add(state)
        self._session.flush()
        return state

    def get_state(self, encounter_id: int) -> Optional[EncounterState]:
        """Get encounter state."""
        return (
            self._session.query(EncounterState)
            .filter_by(encounter_id=encounter_id)
            .first()
        )

    def delete_state(self, state: EncounterState) -> None:
        """Delete encounter state."""
        self._session.delete(state)
        self._session.flush()

    # =========================================================================
    # Combat Log operations
    # =========================================================================

    def add_combat_log(self, log: CombatLog) -> CombatLog:
        """Add a combat log entry."""
        self._session.add(log)
        self._session.flush()
        return log

    def get_combat_logs(
        self,
        encounter_id: int,
        limit: Optional[int] = None,
    ) -> list[CombatLog]:
        """Get combat logs for an encounter."""
        query = (
            self._session.query(CombatLog)
            .filter_by(encounter_id=encounter_id)
            .order_by(CombatLog.created_at.asc())
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_combat_logs_by_round(
        self,
        encounter_id: int,
        round_number: int,
    ) -> list[CombatLog]:
        """Get combat logs for a specific round."""
        return (
            self._session.query(CombatLog)
            .filter_by(encounter_id=encounter_id, round_number=round_number)
            .order_by(CombatLog.created_at.asc())
            .all()
        )

