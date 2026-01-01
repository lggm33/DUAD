"""
Combat event handlers for SocketIO.

Handles all combat-related events: initiative, actions, turn control, and sync.
"""

import logging
from flask_socketio import emit

from app.extensions import db
from app.domain.encounters.encounter_repository import EncounterRepository
from app.domain.encounters.combat_service import CombatService
from app.domain.encounters.models import CombatActionType, EncounterOutcome
from app.domain.characters.character_repository import CharacterRepository
from app.domain.npcs.npc_repository import NPCRepository
from app.domain.games.game_membership_repository import GameMembershipRepository

logger = logging.getLogger(__name__)


def _get_combat_service(session):
    """Create CombatService with all required repositories."""
    return CombatService(
        encounter_repository=EncounterRepository(session),
        character_repository=CharacterRepository(session),
        npc_repository=NPCRepository(session),
        game_membership_repository=GameMembershipRepository(session),
    )


def register_combat_events(socketio, app, shared_state, helpers):
    """Register all combat-related SocketIO events."""

    authenticated_users = shared_state["authenticated_users"]
    get_user_or_error = helpers["get_user_or_error"]

    # =========================================================================
    # Initiative Events
    # =========================================================================

    @socketio.on("roll_initiative")
    def handle_roll_initiative(data):
        """Roll initiative for a combatant."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        combatant_key = data.get("combatant_key")
        roll = data.get("roll")
        modifier = data.get("modifier", 0)

        if not encounter_id or not combatant_key:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id and combatant_key required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.roll_initiative(
                    encounter_id=encounter_id,
                    user_id=user["user_id"],
                    combatant_key=combatant_key,
                    roll=roll,
                    modifier=modifier,
                )
                session.commit()

                emit("initiative_updated", result, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error rolling initiative: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to roll initiative"})

    @socketio.on("set_initiative")
    def handle_set_initiative(data):
        """DM manually sets initiative."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        combatant_key = data.get("combatant_key")
        value = data.get("value")

        if not encounter_id or not combatant_key or value is None:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id, combatant_key, and value required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.set_initiative(
                    encounter_id=encounter_id,
                    dm_user_id=user["user_id"],
                    combatant_key=combatant_key,
                    value=value,
                )
                session.commit()

                emit("initiative_updated", result, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error setting initiative: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to set initiative"})

    # =========================================================================
    # Action Events
    # =========================================================================

    @socketio.on("combat_action")
    def handle_combat_action(data):
        """Log a combat action."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        action_type_str = data.get("action_type")
        actor_key = data.get("actor_key")
        target_key = data.get("target_key")
        action_data = data.get("data", {})
        result = data.get("result")
        hp_change = data.get("hp_change")
        conditions_add = data.get("conditions_add")
        conditions_remove = data.get("conditions_remove")

        if not encounter_id or not action_type_str or not actor_key:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id, action_type, and actor_key required"})
            return

        try:
            action_type = CombatActionType(action_type_str)
        except ValueError:
            emit("error", {"code": "INVALID_DATA", "message": f"Invalid action_type: {action_type_str}"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result_data = combat_service.log_combat_action(
                    encounter_id=encounter_id,
                    user_id=user["user_id"],
                    action_type=action_type,
                    actor_key=actor_key,
                    target_key=target_key,
                    data=action_data,
                    result=result,
                    hp_change=hp_change,
                    conditions_add=conditions_add,
                    conditions_remove=conditions_remove,
                )
                session.commit()

                emit("combat_action_logged", result_data, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error logging action: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to log action"})

    @socketio.on("update_combatant")
    def handle_update_combatant(data):
        """DM updates combatant state."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        combatant_key = data.get("combatant_key")
        changes = data.get("changes", {})

        if not encounter_id or not combatant_key:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id and combatant_key required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.update_combatant(
                    encounter_id=encounter_id,
                    dm_user_id=user["user_id"],
                    combatant_key=combatant_key,
                    changes=changes,
                )
                session.commit()

                emit("combatant_updated", result, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error updating combatant: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to update combatant"})

    # =========================================================================
    # Turn Control Events
    # =========================================================================

    @socketio.on("start_combat")
    def handle_start_combat(data):
        """DM starts combat after initiative is rolled."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        if not encounter_id:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.start_combat(
                    encounter_id=encounter_id,
                    dm_user_id=user["user_id"],
                )
                session.commit()

                game_id = user.get("game_id")
                emit("combat_round_started", {"encounter_id": encounter_id, "round_number": 1}, room=f"game_{game_id}")
                emit("turn_started", result, room=f"game_{game_id}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error starting combat: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to start combat"})

    @socketio.on("next_turn")
    def handle_next_turn(data):
        """DM advances to the next turn."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        if not encounter_id:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.next_turn(
                    encounter_id=encounter_id,
                    dm_user_id=user["user_id"],
                )
                session.commit()

                emit("turn_started", result, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error advancing turn: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to advance turn"})

    @socketio.on("skip_turn")
    def handle_skip_turn(data):
        """DM skips the current turn."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        reason = data.get("reason", "dm_skip")

        if not encounter_id:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)

                state = combat_service._get_state_or_raise(encounter_id)
                skipped = state.initiative_order[state.current_turn_index]

                result = combat_service.skip_turn(
                    encounter_id=encounter_id,
                    dm_user_id=user["user_id"],
                    reason=reason,
                )
                session.commit()

                game_id = user.get("game_id")
                emit("turn_skipped", {"encounter_id": encounter_id, "combatant_key": skipped["key"], "reason": reason}, room=f"game_{game_id}")
                emit("turn_started", result, room=f"game_{game_id}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error skipping turn: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to skip turn"})

    @socketio.on("pause_encounter")
    def handle_pause_encounter(data):
        """DM pauses the encounter."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        reason = data.get("reason", "DM paused")

        if not encounter_id:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.pause_combat(encounter_id=encounter_id, dm_user_id=user["user_id"], reason=reason)
                session.commit()

                emit("encounter_paused", result, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error pausing encounter: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to pause encounter"})

    @socketio.on("resume_encounter")
    def handle_resume_encounter(data):
        """DM resumes the encounter."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        if not encounter_id:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.resume_combat(encounter_id=encounter_id, dm_user_id=user["user_id"])
                session.commit()

                emit("turn_started", result, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error resuming encounter: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to resume encounter"})

    @socketio.on("end_encounter")
    def handle_end_encounter(data):
        """DM ends the encounter."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        outcome_str = data.get("outcome")

        if not encounter_id or not outcome_str:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id and outcome required"})
            return

        try:
            outcome = EncounterOutcome(outcome_str)
        except ValueError:
            emit("error", {"code": "INVALID_DATA", "message": f"Invalid outcome: {outcome_str}"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.end_combat(encounter_id=encounter_id, dm_user_id=user["user_id"], outcome=outcome)
                session.commit()

                emit("encounter_ended", result, room=f"game_{user.get('game_id')}")

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error ending encounter: {e}")
            emit("error", {"code": "COMBAT_FAILED", "message": "Failed to end encounter"})

    # =========================================================================
    # Sync/Reconnection Events
    # =========================================================================

    @socketio.on("sync_encounter_state")
    def handle_sync_encounter_state(data):
        """Client requests current encounter state (for reconnection)."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        if not encounter_id:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                combat_service = _get_combat_service(session)
                result = combat_service.get_state_snapshot(encounter_id=encounter_id, user_id=user["user_id"])

                user["active_encounter_id"] = encounter_id
                emit("encounter_state_sync", result)

        except ValueError as e:
            emit("error", {"code": "COMBAT_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error syncing state: {e}")
            emit("error", {"code": "SYNC_FAILED", "message": "Failed to sync encounter state"})

    @socketio.on("join_encounter")
    def handle_join_encounter(data):
        """Player joins an encounter."""
        user = get_user_or_error()
        if not user:
            return

        encounter_id = data.get("encounter_id")
        character_id = data.get("character_id")

        if not encounter_id:
            emit("error", {"code": "INVALID_DATA", "message": "encounter_id required"})
            return

        user["active_encounter_id"] = encounter_id
        if character_id:
            user["character_id"] = character_id

        game_id = user.get("game_id")
        if game_id:
            emit("player_reconnected_combat", {
                "encounter_id": encounter_id,
                "combatant_key": f"CHARACTER_{character_id}" if character_id else None,
                "player_name": user.get("name") or user.get("username"),
            }, room=f"game_{game_id}")

        logger.info(f"[SocketIO] User {user['username']} joined encounter {encounter_id}")

