"""
Combat Service for real-time combat logic.

Centralizes all combat operations to avoid code duplication between
REST endpoints and WebSocket handlers. Each method:
1. Validates the action
2. Persists changes to the database
3. Returns data ready to be emitted via WebSocket
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Optional, TypedDict

from app.domain.encounters.models import (
    Encounter,
    EncounterState,
    EncounterStatus,
    EncounterStateStatus,
    EncounterOutcome,
    CombatLog,
    CombatActionType,
    ActorType,
    ParticipantType,
)
from app.domain.encounters.encounter_repository import EncounterRepository
from app.domain.characters.character_repository import CharacterRepository
from app.domain.npcs.npc_repository import NPCRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameRoleInGame, GameMembershipStatus


# =============================================================================
# Response Types for WebSocket Emission
# =============================================================================


class InitiativeRollResult(TypedDict):
    """Result of rolling initiative."""

    encounter_id: int
    combatant_key: str
    combatant_name: str
    roll: int
    modifier: int
    total: int
    initiative_order: list[dict[str, Any]]
    all_rolled: bool


class CombatActionResult(TypedDict):
    """Result of a combat action."""

    log_entry: dict[str, Any]
    combatants_state: dict[str, Any]


class TurnResult(TypedDict):
    """Result of turn advancement."""

    encounter_id: int
    round_number: int
    current_combatant: dict[str, Any]
    next_combatant: dict[str, Any] | None
    combatants_state: dict[str, Any]


class EncounterStartResult(TypedDict):
    """Result of starting an encounter."""

    encounter_id: int
    encounter_name: str
    participants: list[dict[str, Any]]
    combatants_state: dict[str, Any]
    status: str


class EncounterEndResult(TypedDict):
    """Result of ending an encounter."""

    encounter_id: int
    outcome: str
    total_rounds: int
    total_actions: int


class CombatantUpdateResult(TypedDict):
    """Result of updating a combatant."""

    encounter_id: int
    combatant_key: str
    changes: dict[str, Any]
    combatants_state: dict[str, Any]


class StateSnapshot(TypedDict):
    """Full state snapshot for sync/reconnection."""

    encounter: dict[str, Any]
    state: dict[str, Any]
    recent_logs: list[dict[str, Any]]


# =============================================================================
# Combat Service
# =============================================================================


class CombatService:
    """
    Service for real-time combat operations.

    All public methods return data ready to be emitted via WebSocket.
    """

    def __init__(
        self,
        encounter_repository: EncounterRepository,
        character_repository: CharacterRepository,
        npc_repository: NPCRepository,
        game_membership_repository: GameMembershipRepository,
    ) -> None:
        self._encounter_repo = encounter_repository
        self._character_repo = character_repository
        self._npc_repo = npc_repository
        self._membership_repo = game_membership_repository

    # =========================================================================
    # Authorization Helpers
    # =========================================================================

    def _verify_is_dm(self, game_id: int, user_id: int) -> None:
        """Verify user is the DM of the game."""
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.role_in_game != GameRoleInGame.DM:
            raise ValueError("Only the DM can perform this action")

    def _verify_is_member(self, game_id: int, user_id: int) -> None:
        """Verify user is an active member of the game."""
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        if not membership or membership.status != GameMembershipStatus.ACTIVE:
            raise ValueError("User is not an active member of this game")

    def _verify_owns_combatant(
        self,
        combatant_key: str,
        user_id: int,
        game_id: int,
    ) -> bool:
        """Check if user owns the combatant (their character)."""
        if not combatant_key.startswith("CHARACTER_"):
            return False

        character_id = int(combatant_key.split("_")[1])
        character = self._character_repo.get_by_id(character_id)

        return character is not None and character.user_id == user_id

    def _get_encounter_or_raise(self, encounter_id: int) -> Encounter:
        """Get encounter or raise if not found."""
        encounter = self._encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise ValueError("Encounter not found")
        return encounter

    def _get_state_or_raise(self, encounter_id: int) -> EncounterState:
        """Get encounter state or raise if not found."""
        state = self._encounter_repo.get_state(encounter_id)
        if not state:
            raise ValueError("Encounter state not found")
        return state

    # =========================================================================
    # Initiative Operations
    # =========================================================================

    def roll_initiative(
        self,
        encounter_id: int,
        user_id: int,
        combatant_key: str,
        roll: Optional[int] = None,
        modifier: int = 0,
    ) -> InitiativeRollResult:
        """
        Roll initiative for a combatant.

        Players can roll for their own character.
        DM can roll for any combatant (usually NPCs).

        Args:
            encounter_id: The encounter ID
            user_id: The user rolling
            combatant_key: The combatant key (e.g., "CHARACTER_5", "NPC_12_1")
            roll: Optional fixed roll (1-20), if None will random
            modifier: Initiative modifier to add

        Returns:
            InitiativeRollResult ready for WebSocket emission
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        if state.status != EncounterStateStatus.ROLLING_INITIATIVE:
            raise ValueError("Not in initiative rolling phase")

        # Authorization: player can roll for their character, DM for anyone
        is_dm = self._is_dm(encounter.game_id, user_id)
        if not is_dm and not self._verify_owns_combatant(
            combatant_key, user_id, encounter.game_id
        ):
            raise ValueError("You can only roll for your own character")

        # Check combatant exists in state
        if combatant_key not in state.combatants_state:
            raise ValueError(f"Combatant {combatant_key} not in encounter")

        # Roll if not provided
        actual_roll = roll if roll is not None else random.randint(1, 20)
        total = actual_roll + modifier

        # Update initiative order
        initiative_order = list(state.initiative_order)

        # Remove existing entry for this combatant if any
        initiative_order = [
            entry for entry in initiative_order if entry["key"] != combatant_key
        ]

        # Add new entry
        combatant_state = state.combatants_state[combatant_key]
        initiative_order.append({
            "key": combatant_key,
            "name": combatant_state["name"],
            "roll": actual_roll,
            "modifier": modifier,
            "total": total,
        })

        # Sort by total (descending), then roll for ties
        initiative_order.sort(key=lambda x: (x["total"], x["roll"]), reverse=True)
        state.initiative_order = initiative_order

        # Check if all have rolled
        all_keys = set(state.combatants_state.keys())
        rolled_keys = {entry["key"] for entry in initiative_order}
        all_rolled = all_keys == rolled_keys

        # Log the action
        self._log_action(
            encounter_id=encounter_id,
            round_number=0,  # Initiative is before round 1
            action_type=CombatActionType.INITIATIVE_ROLL,
            actor_type=self._get_actor_type(combatant_key),
            actor_id=self._get_actor_id(combatant_key),
            actor_name=combatant_state["name"],
            user_id=user_id,
            data={"roll": actual_roll, "modifier": modifier, "total": total},
        )

        return InitiativeRollResult(
            encounter_id=encounter_id,
            combatant_key=combatant_key,
            combatant_name=combatant_state["name"],
            roll=actual_roll,
            modifier=modifier,
            total=total,
            initiative_order=initiative_order,
            all_rolled=all_rolled,
        )

    def set_initiative(
        self,
        encounter_id: int,
        dm_user_id: int,
        combatant_key: str,
        value: int,
    ) -> InitiativeRollResult:
        """
        DM manually sets initiative for a combatant.

        Args:
            encounter_id: The encounter ID
            dm_user_id: The DM user ID
            combatant_key: The combatant key
            value: The initiative value to set

        Returns:
            InitiativeRollResult ready for WebSocket emission
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if combatant_key not in state.combatants_state:
            raise ValueError(f"Combatant {combatant_key} not in encounter")

        # Update initiative order
        initiative_order = list(state.initiative_order)
        initiative_order = [
            entry for entry in initiative_order if entry["key"] != combatant_key
        ]

        combatant_state = state.combatants_state[combatant_key]
        initiative_order.append({
            "key": combatant_key,
            "name": combatant_state["name"],
            "roll": value,
            "modifier": 0,
            "total": value,
        })

        initiative_order.sort(key=lambda x: (x["total"], x["roll"]), reverse=True)
        state.initiative_order = initiative_order

        all_keys = set(state.combatants_state.keys())
        rolled_keys = {entry["key"] for entry in initiative_order}
        all_rolled = all_keys == rolled_keys

        return InitiativeRollResult(
            encounter_id=encounter_id,
            combatant_key=combatant_key,
            combatant_name=combatant_state["name"],
            roll=value,
            modifier=0,
            total=value,
            initiative_order=initiative_order,
            all_rolled=all_rolled,
        )

    # =========================================================================
    # Combat Actions
    # =========================================================================

    def log_combat_action(
        self,
        encounter_id: int,
        user_id: int,
        action_type: CombatActionType,
        actor_key: str,
        target_key: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
        result: Optional[dict[str, Any]] = None,
        hp_change: Optional[int] = None,
        conditions_add: Optional[list[str]] = None,
        conditions_remove: Optional[list[str]] = None,
    ) -> CombatActionResult:
        """
        Log a combat action and update combatant state.

        Args:
            encounter_id: The encounter ID
            user_id: The user performing the action
            action_type: Type of action
            actor_key: The acting combatant key
            target_key: Optional target combatant key
            data: Action data (e.g., attack roll, damage dice)
            result: Action result (e.g., hit/miss, damage dealt)
            hp_change: HP change to apply to target (negative for damage)
            conditions_add: Conditions to add to target
            conditions_remove: Conditions to remove from target

        Returns:
            CombatActionResult ready for WebSocket emission
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        if state.status not in (
            EncounterStateStatus.IN_PROGRESS,
            EncounterStateStatus.ROLLING_INITIATIVE,
        ):
            raise ValueError("Combat is not active")

        # Authorization check
        is_dm = self._is_dm(encounter.game_id, user_id)
        if not is_dm and not self._verify_owns_combatant(
            actor_key, user_id, encounter.game_id
        ):
            raise ValueError("You can only act with your own character")

        # Get actor info
        actor_state = state.combatants_state.get(actor_key)
        if not actor_state:
            raise ValueError(f"Actor {actor_key} not in encounter")

        # Get target info if provided
        target_name = None
        if target_key:
            target_state = state.combatants_state.get(target_key)
            if target_state:
                target_name = target_state["name"]

                # Apply HP change if provided
                if hp_change is not None:
                    current_hp = target_state.get("current_hp", 0)
                    max_hp = target_state.get("max_hp", current_hp)
                    new_hp = max(0, min(max_hp, current_hp + hp_change))
                    target_state["current_hp"] = new_hp

                # Apply condition changes
                if conditions_add:
                    current = target_state.get("conditions", [])
                    target_state["conditions"] = list(set(current + conditions_add))

                if conditions_remove:
                    current = target_state.get("conditions", [])
                    target_state["conditions"] = [
                        c for c in current if c not in conditions_remove
                    ]

        # Log the action
        log = self._log_action(
            encounter_id=encounter_id,
            round_number=state.current_round,
            action_type=action_type,
            actor_type=self._get_actor_type(actor_key),
            actor_id=self._get_actor_id(actor_key),
            actor_name=actor_state["name"],
            user_id=user_id,
            target_type=self._get_actor_type(target_key) if target_key else None,
            target_id=self._get_actor_id(target_key) if target_key else None,
            target_name=target_name,
            data=data,
            result=result,
        )

        return CombatActionResult(
            log_entry=self._log_to_dict(log),
            combatants_state=dict(state.combatants_state),
        )

    def update_combatant(
        self,
        encounter_id: int,
        dm_user_id: int,
        combatant_key: str,
        changes: dict[str, Any],
    ) -> CombatantUpdateResult:
        """
        DM updates combatant state directly.

        Args:
            encounter_id: The encounter ID
            dm_user_id: The DM user ID
            combatant_key: The combatant to update
            changes: Changes to apply (hp, conditions, etc.)

        Returns:
            CombatantUpdateResult ready for WebSocket emission
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if combatant_key not in state.combatants_state:
            raise ValueError(f"Combatant {combatant_key} not in encounter")

        combatant_state = state.combatants_state[combatant_key]

        # Apply changes
        for key, value in changes.items():
            if key in ("current_hp", "temp_hp", "conditions"):
                combatant_state[key] = value

        # Log as DM override
        self._log_action(
            encounter_id=encounter_id,
            round_number=state.current_round,
            action_type=CombatActionType.DM_OVERRIDE,
            actor_type=ActorType.SYSTEM,
            actor_name="DM",
            user_id=dm_user_id,
            target_type=self._get_actor_type(combatant_key),
            target_id=self._get_actor_id(combatant_key),
            target_name=combatant_state["name"],
            data={"changes": changes},
        )

        return CombatantUpdateResult(
            encounter_id=encounter_id,
            combatant_key=combatant_key,
            changes=changes,
            combatants_state=dict(state.combatants_state),
        )

    # =========================================================================
    # Turn Management
    # =========================================================================

    def start_combat(
        self,
        encounter_id: int,
        dm_user_id: int,
    ) -> TurnResult:
        """
        Start combat after initiative is rolled.

        Transitions from ROLLING_INITIATIVE to IN_PROGRESS.

        Args:
            encounter_id: The encounter ID
            dm_user_id: The DM user ID

        Returns:
            TurnResult for the first turn
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if state.status != EncounterStateStatus.ROLLING_INITIATIVE:
            raise ValueError("Combat has already started or ended")

        if not state.initiative_order:
            raise ValueError("Initiative must be rolled before starting combat")

        # Start combat
        state.status = EncounterStateStatus.IN_PROGRESS
        state.current_round = 1
        state.current_turn_index = 0
        state.turn_started_at = datetime.now(timezone.utc)

        # Log round start
        self._log_action(
            encounter_id=encounter_id,
            round_number=1,
            action_type=CombatActionType.TURN_START,
            actor_type=ActorType.SYSTEM,
            actor_name="System",
            user_id=dm_user_id,
            data={"round": 1},
        )

        current = state.initiative_order[0]
        next_combatant = (
            state.initiative_order[1] if len(state.initiative_order) > 1 else None
        )

        return TurnResult(
            encounter_id=encounter_id,
            round_number=1,
            current_combatant=current,
            next_combatant=next_combatant,
            combatants_state=dict(state.combatants_state),
        )

    def next_turn(
        self,
        encounter_id: int,
        dm_user_id: int,
    ) -> TurnResult:
        """
        Advance to the next turn.

        Args:
            encounter_id: The encounter ID
            dm_user_id: The DM user ID

        Returns:
            TurnResult for the new turn
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if state.status != EncounterStateStatus.IN_PROGRESS:
            raise ValueError("Combat is not in progress")

        # Log turn end for current combatant
        current_key = state.initiative_order[state.current_turn_index]["key"]
        current_name = state.initiative_order[state.current_turn_index]["name"]

        self._log_action(
            encounter_id=encounter_id,
            round_number=state.current_round,
            action_type=CombatActionType.TURN_END,
            actor_type=self._get_actor_type(current_key),
            actor_id=self._get_actor_id(current_key),
            actor_name=current_name,
            user_id=dm_user_id,
        )

        # Advance turn
        state.current_turn_index += 1

        # Check if new round
        if state.current_turn_index >= len(state.initiative_order):
            state.current_turn_index = 0
            state.current_round += 1

        state.turn_started_at = datetime.now(timezone.utc)

        # Log turn start
        new_current = state.initiative_order[state.current_turn_index]
        self._log_action(
            encounter_id=encounter_id,
            round_number=state.current_round,
            action_type=CombatActionType.TURN_START,
            actor_type=self._get_actor_type(new_current["key"]),
            actor_id=self._get_actor_id(new_current["key"]),
            actor_name=new_current["name"],
            user_id=dm_user_id,
        )

        next_index = state.current_turn_index + 1
        next_combatant = (
            state.initiative_order[next_index % len(state.initiative_order)]
            if len(state.initiative_order) > 1
            else None
        )

        return TurnResult(
            encounter_id=encounter_id,
            round_number=state.current_round,
            current_combatant=new_current,
            next_combatant=next_combatant,
            combatants_state=dict(state.combatants_state),
        )

    def skip_turn(
        self,
        encounter_id: int,
        dm_user_id: int,
        reason: str = "dm_skip",
    ) -> TurnResult:
        """
        Skip the current turn.

        Args:
            encounter_id: The encounter ID
            dm_user_id: The DM user ID
            reason: Reason for skip ("timeout", "dm_skip", "disconnected")

        Returns:
            TurnResult for the new turn
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        current = state.initiative_order[state.current_turn_index]

        # Log the skip
        self._log_action(
            encounter_id=encounter_id,
            round_number=state.current_round,
            action_type=CombatActionType.TURN_SKIPPED,
            actor_type=self._get_actor_type(current["key"]),
            actor_id=self._get_actor_id(current["key"]),
            actor_name=current["name"],
            user_id=dm_user_id,
            data={"reason": reason},
        )

        # Advance turn
        return self.next_turn(encounter_id, dm_user_id)

    # =========================================================================
    # Encounter State Management
    # =========================================================================

    def pause_combat(
        self,
        encounter_id: int,
        dm_user_id: int,
        reason: str = "DM paused",
    ) -> dict[str, Any]:
        """Pause combat."""
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if state.status != EncounterStateStatus.IN_PROGRESS:
            raise ValueError("Combat is not in progress")

        state.status = EncounterStateStatus.PAUSED
        encounter.status = EncounterStatus.PAUSED

        return {"encounter_id": encounter_id, "reason": reason}

    def resume_combat(
        self,
        encounter_id: int,
        dm_user_id: int,
    ) -> TurnResult:
        """Resume paused combat."""
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        if state.status != EncounterStateStatus.PAUSED:
            raise ValueError("Combat is not paused")

        state.status = EncounterStateStatus.IN_PROGRESS
        encounter.status = EncounterStatus.ACTIVE
        state.turn_started_at = datetime.now(timezone.utc)

        current = state.initiative_order[state.current_turn_index]
        next_index = state.current_turn_index + 1
        next_combatant = (
            state.initiative_order[next_index % len(state.initiative_order)]
            if len(state.initiative_order) > 1
            else None
        )

        return TurnResult(
            encounter_id=encounter_id,
            round_number=state.current_round,
            current_combatant=current,
            next_combatant=next_combatant,
            combatants_state=dict(state.combatants_state),
        )

    def end_combat(
        self,
        encounter_id: int,
        dm_user_id: int,
        outcome: EncounterOutcome,
    ) -> EncounterEndResult:
        """End combat with an outcome."""
        encounter = self._get_encounter_or_raise(encounter_id)
        state = self._get_state_or_raise(encounter_id)

        self._verify_is_dm(encounter.game_id, dm_user_id)

        # Update states
        state.status = EncounterStateStatus.ENDED
        encounter.status = EncounterStatus.COMPLETED
        encounter.outcome = outcome

        # Get log count
        logs = self._encounter_repo.get_combat_logs(encounter_id)

        return EncounterEndResult(
            encounter_id=encounter_id,
            outcome=outcome.value,
            total_rounds=state.current_round,
            total_actions=len(logs),
        )

    # =========================================================================
    # State Sync (for reconnection)
    # =========================================================================

    def get_state_snapshot(
        self,
        encounter_id: int,
        user_id: int,
    ) -> StateSnapshot:
        """
        Get full state snapshot for sync/reconnection.

        Args:
            encounter_id: The encounter ID
            user_id: The requesting user

        Returns:
            StateSnapshot with encounter, state, and recent logs
        """
        encounter = self._get_encounter_or_raise(encounter_id)
        self._verify_is_member(encounter.game_id, user_id)

        state = self._encounter_repo.get_state(encounter_id)
        logs = self._encounter_repo.get_combat_logs(encounter_id, limit=50)

        return StateSnapshot(
            encounter={
                "id": encounter.id,
                "name": encounter.name,
                "status": encounter.status.value,
                "game_id": encounter.game_id,
            },
            state={
                "current_round": state.current_round if state else 0,
                "current_turn_index": state.current_turn_index if state else 0,
                "initiative_order": state.initiative_order if state else [],
                "combatants_state": state.combatants_state if state else {},
                "status": state.status.value if state else None,
            },
            recent_logs=[self._log_to_dict(log) for log in logs],
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _is_dm(self, game_id: int, user_id: int) -> bool:
        """Check if user is the DM."""
        membership = self._membership_repo.get_game_membership_by_game_id_and_user_id(
            game_id, user_id
        )
        return membership is not None and membership.role_in_game == GameRoleInGame.DM

    def _get_actor_type(self, combatant_key: str) -> ActorType:
        """Get ActorType from combatant key."""
        if combatant_key.startswith("CHARACTER_"):
            return ActorType.CHARACTER
        elif combatant_key.startswith("NPC_"):
            return ActorType.NPC
        return ActorType.SYSTEM

    def _get_actor_id(self, combatant_key: str) -> Optional[int]:
        """Extract actor ID from combatant key."""
        parts = combatant_key.split("_")
        if len(parts) >= 2:
            try:
                return int(parts[1])
            except ValueError:
                pass
        return None

    def _log_action(
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
        """Create and persist a combat log entry."""
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

    def _log_to_dict(self, log: CombatLog) -> dict[str, Any]:
        """Convert CombatLog to dictionary for emission."""
        return {
            "id": log.id,
            "encounter_id": log.encounter_id,
            "round_number": log.round_number,
            "action_type": log.action_type.value,
            "actor_type": log.actor_type.value,
            "actor_id": log.actor_id,
            "actor_name": log.actor_name,
            "target_type": log.target_type.value if log.target_type else None,
            "target_id": log.target_id,
            "target_name": log.target_name,
            "data": log.data,
            "result": log.result,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

