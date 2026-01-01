"""
Encounter API routes.

Endpoints:
- POST /api/v1/game/<game_id>/encounter - Create a new encounter
- GET /api/v1/game/<game_id>/encounters - List all encounters in a game
- GET /api/v1/game/<game_id>/encounter/<encounter_id> - Get a specific encounter
- PUT /api/v1/game/<game_id>/encounter/<encounter_id> - Update an encounter
- DELETE /api/v1/game/<game_id>/encounter/<encounter_id> - Delete an encounter
- GET /api/v1/game/<game_id>/encounter/<encounter_id>/logs - Get combat history
- GET /api/v1/game/<game_id>/encounter/<encounter_id>/state - Get combat state (for reconnection)
"""

from flask import Blueprint, request, jsonify, g

from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response
from app.presentation.encounters.presenters import EncounterPresenter
from app.domain.encounters.encounter_service import EncounterService
from app.domain.encounters.encounter_repository import EncounterRepository
from app.domain.encounters.models import (
    EncounterStatus,
    EncounterDifficulty,
)
from app.domain.characters.character_repository import CharacterRepository
from app.domain.npcs.npc_repository import NPCRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameRoleInGame, GameMembershipStatus
from app.extensions import db


encounter_bp = Blueprint("encounter", __name__, url_prefix="/api/v1/game")


def get_encounter_service() -> EncounterService:
    """Create and return an EncounterService instance."""
    session = db.get_session()
    return EncounterService(
        encounter_repository=EncounterRepository(session),
        character_repository=CharacterRepository(session),
        npc_repository=NPCRepository(session),
        game_repository=GameRepository(session),
        game_membership_repository=GameMembershipRepository(session),
    )


def _is_dm(game_id: int, user_id: int) -> bool:
    """Check if user is the DM of the game."""
    session = db.get_session()
    membership_repo = GameMembershipRepository(session)
    membership = membership_repo.get_game_membership_by_game_id_and_user_id(
        game_id, user_id
    )
    return (
        membership is not None
        and membership.role_in_game == GameRoleInGame.DM
        and membership.status == GameMembershipStatus.ACTIVE
    )


def _parse_encounter_status(value: str) -> EncounterStatus | None:
    """Parse encounter status from string."""
    try:
        return EncounterStatus(value.upper())
    except (ValueError, AttributeError):
        return None


def _parse_encounter_difficulty(value: str) -> EncounterDifficulty | None:
    """Parse encounter difficulty from string."""
    try:
        return EncounterDifficulty(value.upper())
    except (ValueError, AttributeError):
        return None


@encounter_bp.post("/<int:game_id>/encounter")
@auth_required
def create_encounter(game_id: int):
    """
    Create a new encounter in the game.

    Only the DM can create encounters.

    Request body:
    {
        "name": "Encounter Name",
        "description": "Optional description",
        "location": "Optional location",
        "difficulty": "TRIVIAL" | "EASY" | "MEDIUM" | "HARD" | "DEADLY",
        "estimated_xp": 100,
        "notes": "DM notes"
    }

    Returns 201 with the created encounter.
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    description = data.get("description")
    location = data.get("location")
    difficulty_str = data.get("difficulty")
    estimated_xp = data.get("estimated_xp")
    notes = data.get("notes")

    if not name or not name.strip():
        return error_response(
            "VALIDATION_ERROR",
            "Encounter name is required",
            status_code=400,
        )

    difficulty = None
    if difficulty_str:
        difficulty = _parse_encounter_difficulty(difficulty_str)
        if difficulty is None:
            valid_difficulties = [d.value for d in EncounterDifficulty]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid difficulty. Valid values: {valid_difficulties}",
                status_code=400,
            )

    if estimated_xp is not None and not isinstance(estimated_xp, int):
        return error_response(
            "VALIDATION_ERROR",
            "estimated_xp must be an integer",
            status_code=400,
        )

    encounter_service = get_encounter_service()

    try:
        encounter = encounter_service.create_encounter(
            game_id=game_id,
            dm_user_id=g.auth_user.user_id,
            name=name.strip(),
            description=description,
            location=location,
            difficulty=difficulty,
            estimated_xp=estimated_xp,
            notes=notes,
        )
        db.get_session().commit()
        return jsonify(EncounterPresenter.encounter_with_participants(encounter)), 201
    except ValueError as e:
        error_msg = str(e).lower()
        if "game not found" in error_msg:
            return error_response("GAME_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@encounter_bp.get("/<int:game_id>/encounters")
@auth_required
def get_game_encounters(game_id: int):
    """
    Get all encounters in a game.

    Query params:
    - status: string (optional) - Filter by encounter status

    Returns list of encounters with participants.
    """
    status_str = request.args.get("status")

    status = None
    if status_str:
        status = _parse_encounter_status(status_str)
        if status is None:
            valid_statuses = [s.value for s in EncounterStatus]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid status filter. Valid values: {valid_statuses}",
                status_code=400,
            )

    encounter_service = get_encounter_service()

    try:
        encounters = encounter_service.get_game_encounters(
            game_id=game_id,
            user_id=g.auth_user.user_id,
            status=status,
        )
        return jsonify([
            EncounterPresenter.encounter_with_participants(enc)
            for enc in encounters
        ]), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "not an active member" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@encounter_bp.get("/<int:game_id>/encounter/<int:encounter_id>")
@auth_required
def get_encounter(game_id: int, encounter_id: int):
    """
    Get a specific encounter by ID.

    Returns the encounter with participants.
    """
    encounter_service = get_encounter_service()

    try:
        encounter = encounter_service.get_encounter(
            encounter_id=encounter_id,
            user_id=g.auth_user.user_id,
        )
    except ValueError as e:
        error_msg = str(e).lower()
        if "not an active member" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

    if not encounter:
        return error_response(
            "ENCOUNTER_NOT_FOUND",
            "Encounter not found",
            status_code=404,
        )

    if encounter.game_id != game_id:
        return error_response(
            "ENCOUNTER_NOT_FOUND",
            "Encounter not found in this game",
            status_code=404,
        )

    return jsonify(EncounterPresenter.encounter_with_participants(encounter)), 200


@encounter_bp.put("/<int:game_id>/encounter/<int:encounter_id>")
@auth_required
def update_encounter(game_id: int, encounter_id: int):
    """
    Update an encounter's data.

    Only the DM can update encounters.
    Cannot update an active encounter.

    Request body (all fields optional):
    {
        "name": "New Name",
        "description": "New description",
        "location": "New location",
        "difficulty": "HARD",
        "estimated_xp": 200,
        "notes": "New notes"
    }

    Returns the updated encounter.
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    description = data.get("description")
    location = data.get("location")
    difficulty_str = data.get("difficulty")
    estimated_xp = data.get("estimated_xp")
    notes = data.get("notes")

    if name is not None and (not name or not name.strip()):
        return error_response(
            "VALIDATION_ERROR",
            "Encounter name cannot be empty",
            status_code=400,
        )

    difficulty = None
    if difficulty_str:
        difficulty = _parse_encounter_difficulty(difficulty_str)
        if difficulty is None:
            valid_difficulties = [d.value for d in EncounterDifficulty]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid difficulty. Valid values: {valid_difficulties}",
                status_code=400,
            )

    if estimated_xp is not None and not isinstance(estimated_xp, int):
        return error_response(
            "VALIDATION_ERROR",
            "estimated_xp must be an integer",
            status_code=400,
        )

    encounter_service = get_encounter_service()

    try:
        # First verify the encounter belongs to this game
        encounter = encounter_service.get_encounter(encounter_id, g.auth_user.user_id)
        if not encounter or encounter.game_id != game_id:
            return error_response(
                "ENCOUNTER_NOT_FOUND",
                "Encounter not found in this game",
                status_code=404,
            )

        updated_encounter = encounter_service.update_encounter(
            encounter_id=encounter_id,
            dm_user_id=g.auth_user.user_id,
            name=name.strip() if name else None,
            description=description,
            location=location,
            difficulty=difficulty,
            estimated_xp=estimated_xp,
            notes=notes,
        )
        db.get_session().commit()
        return jsonify(EncounterPresenter.encounter_with_participants(updated_encounter)), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("ENCOUNTER_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        if "cannot modify an active" in error_msg:
            return error_response("CONFLICT", str(e), status_code=409)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@encounter_bp.delete("/<int:game_id>/encounter/<int:encounter_id>")
@auth_required
def delete_encounter(game_id: int, encounter_id: int):
    """
    Delete an encounter.

    Only the DM can delete encounters.
    Cannot delete an active encounter.

    Returns 204 No Content on success.
    """
    encounter_service = get_encounter_service()

    try:
        # First verify the encounter belongs to this game
        encounter = encounter_service.get_encounter(encounter_id, g.auth_user.user_id)
        if not encounter or encounter.game_id != game_id:
            return error_response(
                "ENCOUNTER_NOT_FOUND",
                "Encounter not found in this game",
                status_code=404,
            )

        encounter_service.delete_encounter(
            encounter_id=encounter_id,
            dm_user_id=g.auth_user.user_id,
        )
        db.get_session().commit()
        return "", 204
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("ENCOUNTER_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        if "cannot delete an active" in error_msg:
            return error_response("CONFLICT", str(e), status_code=409)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@encounter_bp.get("/<int:game_id>/encounter/<int:encounter_id>/logs")
@auth_required
def get_encounter_logs(game_id: int, encounter_id: int):
    """
    Get combat log history for an encounter.

    Query params:
    - round: int (optional) - Filter by round number
    - limit: int (optional) - Limit number of logs (default: 100)

    Returns list of combat log entries.
    """
    round_number = request.args.get("round", type=int)
    limit = request.args.get("limit", default=100, type=int)
    limit = min(limit, 500)  # Cap at 500 logs

    encounter_service = get_encounter_service()

    try:
        # First verify the encounter belongs to this game
        encounter = encounter_service.get_encounter(encounter_id, g.auth_user.user_id)
        if not encounter or encounter.game_id != game_id:
            return error_response(
                "ENCOUNTER_NOT_FOUND",
                "Encounter not found in this game",
                status_code=404,
            )

        logs = encounter_service.get_combat_logs(
            encounter_id=encounter_id,
            user_id=g.auth_user.user_id,
            round_number=round_number,
            limit=limit if round_number is None else None,
        )
        return jsonify(EncounterPresenter.combat_logs_collection(logs)), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("ENCOUNTER_NOT_FOUND", str(e), status_code=404)
        if "not an active member" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@encounter_bp.get("/<int:game_id>/encounter/<int:encounter_id>/state")
@auth_required
def get_encounter_state(game_id: int, encounter_id: int):
    """
    Get current combat state for an encounter.

    Used for client reconnection to sync state mid-combat.

    Returns:
        - encounter: Basic encounter info with participants
        - state: Current EncounterState (if active combat)
        - recent_logs: Recent combat log entries

    Errors:
        - 404: Encounter not found
        - 403: User not a member of the game
    """
    encounter_service = get_encounter_service()

    try:
        result = encounter_service.get_encounter_state_for_reconnect(
            encounter_id=encounter_id,
            user_id=g.auth_user.user_id,
            recent_logs_limit=20,
        )
    except ValueError as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return error_response("NOT_FOUND", str(e), status_code=404)
        if "not an active member" in error_message:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

    # Verify encounter belongs to the game from the URL
    if result["encounter"].game_id != game_id:
        return error_response(
            "NOT_FOUND",
            "Encounter not found in this game",
            status_code=404,
        )

    response_data = EncounterPresenter.encounter_state_for_reconnect(
        encounter=result["encounter"],
        state=result["state"],
        recent_logs=result["recent_logs"],
    )

    return jsonify(response_data), 200
