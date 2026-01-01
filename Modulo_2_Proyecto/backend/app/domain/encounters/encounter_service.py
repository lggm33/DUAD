"""
Service for Encounter business logic.

Handles encounter creation, participant management, and state transitions.
Combat logic (turns, initiative) is handled by CombatService.
"""

from __future__ import annotations

from typing import Any, Optional

from app.domain.encounters.models import (
    Encounter,
    EncounterParticipant,
    EncounterState,
    EncounterStatus,
    EncounterDifficulty,
    EncounterOutcome,
    EncounterStateStatus,
    ParticipantType,
    CombatLog,
    CombatActionType,
    ActorType,
)
from app.domain.encounters.encounter_repository import EncounterRepository
from app.domain.characters.character_repository import CharacterRepository
from app.domain.npcs.npc_repository import NPCRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameRoleInGame, GameMembershipStatus


class EncounterService:
    """Service for encounter operations."""

    def __init__(
        self,
        encounter_repository: EncounterRepository,
        character_repository: CharacterRepository,
        npc_repository: NPCRepository,
        game_repository: GameRepository,
        game_membership_repository: GameMembershipRepository,
    ) -> None:
        self._encounter_repo = encounter_repository
        self._character_repo = character_repository
        self._npc_repo = npc_repository
        self._game_repo = game_repository
        self._membership_repo = game_membership_repository

    # =========================================================================
    # Authorization helpers
    # =========================================================================

    def _verify_is_dm(self, game_id: int, user_id: int) -> None:
        """Verify user is the DM of the game."""
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise ValueError("Only the DM can manage encounters")

    def _verify_is_member(self, game_id: int, user_id: int) -> None:
        """Verify user is an active member of the game."""
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            raise ValueError("User is not an active member of this game")

    def _verify_game_exists(self, game_id: int) -> None:
        """Verify game exists."""
        game = self._game_repo.get_game_by_id(game_id)
        if not game:
            raise ValueError("Game not found")

    # =========================================================================
    # Encounter CRUD
    # =========================================================================

    def create_encounter(
        self,
        game_id: int,
        dm_user_id: int,
        name: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        difficulty: Optional[EncounterDifficulty] = None,
        estimated_xp: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Encounter:
        """
        Create a new encounter.

        Args:
            game_id: The game ID
            dm_user_id: The DM user ID
            name: Encounter name
            description: Optional description
            location: Optional location
            difficulty: Optional difficulty rating
            estimated_xp: Optional XP reward
            notes: DM notes

        Returns:
            The created encounter in DRAFT status

        Raises:
            ValueError: If user is not the DM
        """
        self._verify_game_exists(game_id)
        self._verify_is_dm(game_id, dm_user_id)

        encounter = Encounter(
            game_id=game_id,
            name=name,
            description=description,
            location=location,
            status=EncounterStatus.DRAFT,
            difficulty=difficulty,
            estimated_xp=estimated_xp,
            notes=notes,
        )

        return self._encounter_repo.create(encounter)

    def update_encounter(
        self,
        encounter_id: int,
        dm_user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        difficulty: Optional[EncounterDifficulty] = None,
        estimated_xp: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Encounter:
        """Update an encounter."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status == EncounterStatus.ACTIVE:
            raise ValueError("Cannot modify an active encounter")

        if name is not None:
            encounter.name = name
        if description is not None:
            encounter.description = description
        if location is not None:
            encounter.location = location
        if difficulty is not None:
            encounter.difficulty = difficulty
        if estimated_xp is not None:
            encounter.estimated_xp = estimated_xp
        if notes is not None:
            encounter.notes = notes

        return encounter

    def delete_encounter(self, encounter_id: int, dm_user_id: int) -> bool:
        """Delete an encounter."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status == EncounterStatus.ACTIVE:
            raise ValueError("Cannot delete an active encounter")

        self._encounter_repo.delete(encounter)
        return True

    def get_encounter(
        self,
        encounter_id: int,
        user_id: int,
    ) -> Optional[Encounter]:
        """Get an encounter by ID."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            return None

        self._verify_is_member(encounter.game_id, user_id)
        return encounter

    def get_game_encounters(
        self,
        game_id: int,
        user_id: int,
        status: Optional[EncounterStatus] = None,
    ) -> list[Encounter]:
        """Get encounters in a game."""
        self._verify_is_member(game_id, user_id)

        if status:
            return self._encounter_repo.get_by_status(game_id, status)
        return self._encounter_repo.get_by_game_id(game_id)

    # =========================================================================
    # Participant Management
    # =========================================================================

    def add_character_to_encounter(
        self,
        encounter_id: int,
        character_id: int,
        dm_user_id: int,
        notes: Optional[str] = None,
    ) -> EncounterParticipant:
        """Add a player character to an encounter."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status not in (EncounterStatus.DRAFT, EncounterStatus.READY):
            raise ValueError("Cannot add participants to an active encounter")

        # Verify character exists and belongs to this game
        character = self._character_repo.get_by_id(character_id)
        if not character or character.game_id != encounter.game_id:
            raise ValueError("Character not found in this game")

        participant = EncounterParticipant(
            encounter_id=encounter_id,
            participant_type=ParticipantType.CHARACTER,
            participant_id=character_id,
            quantity=1,
            instance_index=1,
            notes=notes,
        )

        return self._encounter_repo.add_participant(participant)

    def add_npc_to_encounter(
        self,
        encounter_id: int,
        npc_id: int,
        dm_user_id: int,
        quantity: int = 1,
        notes: Optional[str] = None,
    ) -> list[EncounterParticipant]:
        """
        Add NPCs to an encounter.

        Creates multiple participants for quantity > 1 (e.g., 3 Goblins).

        Args:
            encounter_id: The encounter ID
            npc_id: The NPC ID
            dm_user_id: The DM user ID
            quantity: Number of this NPC type
            notes: Optional notes

        Returns:
            List of created participants
        """
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status not in (EncounterStatus.DRAFT, EncounterStatus.READY):
            raise ValueError("Cannot add participants to an active encounter")

        # Verify NPC exists and belongs to this game
        npc = self._npc_repo.get_by_id(npc_id)
        if not npc or npc.game_id != encounter.game_id:
            raise ValueError("NPC not found in this game")

        participants = []
        for i in range(1, quantity + 1):
            participant = EncounterParticipant(
                encounter_id=encounter_id,
                participant_type=ParticipantType.NPC,
                participant_id=npc_id,
                quantity=1,
                instance_index=i,
                notes=notes,
            )
            created = self._encounter_repo.add_participant(participant)
            participants.append(created)

        return participants

    def remove_participant(
        self,
        participant_id: int,
        dm_user_id: int,
    ) -> bool:
        """Remove a participant from an encounter."""
        participants = self._encounter_repo.get_participants(participant_id)
        # Find participant by ID across all encounters
        # This is a simplified implementation
        raise NotImplementedError("Need to implement participant lookup by ID")

    # =========================================================================
    # State Management
    # =========================================================================

    def mark_ready(self, encounter_id: int, dm_user_id: int) -> Encounter:
        """Mark encounter as ready to start."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status != EncounterStatus.DRAFT:
            raise ValueError("Only DRAFT encounters can be marked ready")

        if not encounter.participants:
            raise ValueError("Encounter must have at least one participant")

        encounter.status = EncounterStatus.READY
        return encounter

    def start_encounter(self, encounter_id: int, dm_user_id: int) -> EncounterState:
        """
        Start combat for an encounter.

        Creates the EncounterState and sets status to ACTIVE.
        Initiative should be rolled separately.

        Args:
            encounter_id: The encounter ID
            dm_user_id: The DM user ID

        Returns:
            The created EncounterState

        Raises:
            ValueError: If encounter not ready or user not DM
        """
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status != EncounterStatus.READY:
            raise ValueError("Encounter must be READY to start")

        # Create initial state
        state = EncounterState(
            encounter_id=encounter_id,
            current_round=1,
            current_turn_index=0,
            initiative_order=[],
            combatants_state=self._build_initial_combatants_state(encounter),
            status=EncounterStateStatus.ROLLING_INITIATIVE,
        )

        self._encounter_repo.create_state(state)
        encounter.status = EncounterStatus.ACTIVE

        return state

    def pause_encounter(self, encounter_id: int, dm_user_id: int) -> Encounter:
        """Pause an active encounter."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status != EncounterStatus.ACTIVE:
            raise ValueError("Only ACTIVE encounters can be paused")

        encounter.status = EncounterStatus.PAUSED

        if encounter.state:
            encounter.state.status = EncounterStateStatus.PAUSED

        return encounter

    def resume_encounter(self, encounter_id: int, dm_user_id: int) -> Encounter:
        """Resume a paused encounter."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status != EncounterStatus.PAUSED:
            raise ValueError("Only PAUSED encounters can be resumed")

        encounter.status = EncounterStatus.ACTIVE

        if encounter.state:
            encounter.state.status = EncounterStateStatus.IN_PROGRESS

        return encounter

    def end_encounter(
        self,
        encounter_id: int,
        dm_user_id: int,
        outcome: EncounterOutcome,
    ) -> Encounter:
        """End an encounter with an outcome."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if encounter.status not in (EncounterStatus.ACTIVE, EncounterStatus.PAUSED):
            raise ValueError("Only ACTIVE or PAUSED encounters can be ended")

        encounter.status = EncounterStatus.COMPLETED
        encounter.outcome = outcome

        if encounter.state:
            encounter.state.status = EncounterStateStatus.ENDED

        return encounter

    # =========================================================================
    # Combat Log
    # =========================================================================

    def log_action(
        self,
        encounter_id: int,
        round_number: int,
        action_type: CombatActionType,
        actor_type: ActorType,
        actor_name: str,
        user_id: int,
        actor_id: Optional[int] = None,
        target_type: Optional[ActorType] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
        result: Optional[dict[str, Any]] = None,
    ) -> CombatLog:
        """Log a combat action."""
        log = CombatLog(
            encounter_id=encounter_id,
            round_number=round_number,
            action_type=action_type,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            data=data or {},
            result=result,
            created_by_user_id=user_id,
        )

        return self._encounter_repo.add_combat_log(log)

    def get_combat_logs(
        self,
        encounter_id: int,
        user_id: int,
        round_number: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[CombatLog]:
        """Get combat logs for an encounter."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")

        self._verify_is_member(encounter.game_id, user_id)

        if round_number is not None:
            return self._encounter_repo.get_combat_logs_by_round(
                encounter_id, round_number
            )
        return self._encounter_repo.get_combat_logs(encounter_id, limit)

    # =========================================================================
    # Helper methods
    # =========================================================================

    def _build_initial_combatants_state(
        self,
        encounter: Encounter,
    ) -> dict[str, Any]:
        """Build initial combatants state from participants."""
        state: dict[str, Any] = {}

        for participant in encounter.participants:
            if participant.participant_type == ParticipantType.CHARACTER:
                character = self._character_repo.get_by_id(participant.participant_id)
                if character:
                    key = f"CHARACTER_{character.id}"
                    state[key] = {
                        "name": character.name,
                        "current_hp": character.data.get("hp", 0),
                        "max_hp": character.data.get("max_hp", 0),
                        "temp_hp": 0,
                        "conditions": [],
                        "connection_status": "CONNECTED",
                        "disconnected_at": None,
                        "grace_period_ends": None,
                    }
            else:  # NPC
                npc = self._npc_repo.get_by_id(participant.participant_id)
                if npc:
                    key = f"NPC_{npc.id}_{participant.instance_index}"
                    state[key] = {
                        "name": f"{npc.name} {participant.instance_index}"
                        if participant.instance_index > 1
                        else npc.name,
                        "current_hp": npc.stats.get("hp", 0),
                        "max_hp": npc.stats.get("max_hp", npc.stats.get("hp", 0)),
                        "conditions": [],
                        "connection_status": None,  # NPCs don't have connection status
                    }

        return state

