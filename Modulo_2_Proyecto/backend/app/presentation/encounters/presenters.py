"""
Presenters for Encounter and combat state entities.
"""

from __future__ import annotations

from typing import Any

from app.presentation.base import Presenter
from app.domain.encounters.models import (
    Encounter,
    EncounterParticipant,
    EncounterState,
    CombatLog,
)


class EncounterPresenter(Presenter):
    """
    Presenter for Encounter and related combat state entities.
    """

    @staticmethod
    def encounter_basic(encounter: Encounter) -> dict[str, Any]:
        """
        Returns basic encounter info (no state or logs).
        """
        return {
            "id": encounter.id,
            "game_id": encounter.game_id,
            "name": encounter.name,
            "description": encounter.description,
            "location": encounter.location,
            "status": encounter.status.value,
            "difficulty": encounter.difficulty.value if encounter.difficulty else None,
            "estimated_xp": encounter.estimated_xp,
            "outcome": encounter.outcome.value if encounter.outcome else None,
            "notes": encounter.notes,
            "created_at": (
                encounter.created_at.isoformat() if encounter.created_at else None
            ),
            "updated_at": (
                encounter.updated_at.isoformat() if encounter.updated_at else None
            ),
        }

    @staticmethod
    def participant(participant: EncounterParticipant) -> dict[str, Any]:
        """
        Returns participant info.
        """
        return {
            "id": participant.id,
            "encounter_id": participant.encounter_id,
            "participant_type": participant.participant_type.value,
            "participant_id": participant.participant_id,
            "quantity": participant.quantity,
            "instance_index": participant.instance_index,
            "notes": participant.notes,
        }

    @staticmethod
    def encounter_state(state: EncounterState) -> dict[str, Any]:
        """
        Returns combat state info.
        """
        return {
            "id": state.id,
            "encounter_id": state.encounter_id,
            "current_round": state.current_round,
            "current_turn_index": state.current_turn_index,
            "initiative_order": state.initiative_order,
            "combatants_state": state.combatants_state,
            "turn_started_at": (
                state.turn_started_at.isoformat() if state.turn_started_at else None
            ),
            "status": state.status.value,
            "updated_at": state.updated_at.isoformat() if state.updated_at else None,
        }

    @staticmethod
    def combat_log(log: CombatLog) -> dict[str, Any]:
        """
        Returns combat log entry info.
        """
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
            "created_by_user_id": log.created_by_user_id,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    @staticmethod
    def combat_logs_collection(logs: list[CombatLog]) -> list[dict[str, Any]]:
        """
        Returns a list of combat log entries.
        """
        return [EncounterPresenter.combat_log(log) for log in logs]

    @staticmethod
    def encounter_with_participants(encounter: Encounter) -> dict[str, Any]:
        """
        Returns encounter with participants list.
        """
        return {
            **EncounterPresenter.encounter_basic(encounter),
            "participants": [
                EncounterPresenter.participant(p) for p in encounter.participants
            ],
        }

    @staticmethod
    def encounter_state_for_reconnect(
        encounter: Encounter,
        state: EncounterState | None,
        recent_logs: list[CombatLog],
    ) -> dict[str, Any]:
        """
        Returns full state for client reconnection.

        Includes:
        - Encounter info with participants
        - Current combat state (if active)
        - Recent combat logs for context

        This is used when a client reconnects mid-combat to sync their state.
        """
        return {
            "encounter": EncounterPresenter.encounter_with_participants(encounter),
            "state": EncounterPresenter.encounter_state(state) if state else None,
            "recent_logs": EncounterPresenter.combat_logs_collection(recent_logs),
        }

