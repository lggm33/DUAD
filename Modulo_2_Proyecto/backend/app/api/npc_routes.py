"""
NPC endpoints for Non-Player Character management.

Only the DM can create, update, and delete NPCs.
All game members can view NPCs.
"""

from flask import Blueprint, request, jsonify, g

from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response
from app.presentation.npcs.presenters import NPCPresenter
from app.presentation.characters.presenters import CharacterPresenter
from app.domain.npcs.npc_service import NPCService
from app.domain.npcs.npc_repository import NPCRepository
from app.domain.npcs.models import NPCType, NPCStatus
from app.domain.characters.character_repository import CharacterRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameRoleInGame, GameMembershipStatus
from app.extensions import db


npc_bp = Blueprint("npc", __name__, url_prefix="/api/v1/game")


def get_npc_service() -> NPCService:
    session = db.get_session()
    npc_repo = NPCRepository(session)
    character_repo = CharacterRepository(session)
    game_repo = GameRepository(session)
    membership_repo = GameMembershipRepository(session)
    return NPCService(npc_repo, character_repo, game_repo, membership_repo)


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


def _parse_npc_type(value: str) -> NPCType | None:
    """Parse NPC type from string."""
    try:
        return NPCType(value.upper())
    except (ValueError, AttributeError):
        return None


def _parse_npc_status(value: str) -> NPCStatus | None:
    """Parse NPC status from string."""
    try:
        return NPCStatus(value.upper())
    except (ValueError, AttributeError):
        return None


@npc_bp.post("/<int:game_id>/npc")
@auth_required
def create_npc(game_id: int):
    """
    Create a new NPC in the game.

    Only the DM can create NPCs.

    Request body:
    {
        "name": "NPC Name",
        "npc_type": "ALLY" | "ENEMY" | "NEUTRAL" | "BOSS" | "COMPANION",
        "description": "Optional description",
        "stats": { ... combat stats ... },
        "data": { ... full character data ... }
    }

    Returns 201 with the created NPC.
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    npc_type_str = data.get("npc_type", "NEUTRAL")
    description = data.get("description")
    stats = data.get("stats", {})
    npc_data = data.get("data", {})

    if not name or not name.strip():
        return error_response(
            "VALIDATION_ERROR",
            "NPC name is required",
            status_code=400,
        )

    npc_type = _parse_npc_type(npc_type_str)
    if npc_type is None:
        valid_types = [t.value for t in NPCType]
        return error_response(
            "VALIDATION_ERROR",
            f"Invalid npc_type. Valid values: {valid_types}",
            status_code=400,
        )

    npc_service = get_npc_service()

    try:
        npc = npc_service.create_npc(
            game_id=game_id,
            dm_user_id=g.auth_user.user_id,
            name=name.strip(),
            npc_type=npc_type,
            description=description,
            stats=stats,
            data=npc_data,
        )
        db.get_session().commit()
        return jsonify(NPCPresenter.public(npc)), 201
    except ValueError as e:
        error_msg = str(e).lower()
        if "game not found" in error_msg:
            return error_response("GAME_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@npc_bp.get("/<int:game_id>/npcs")
@auth_required
def get_game_npcs(game_id: int):
    """
    Get all NPCs in a game.

    Query params:
    - active_only: bool (optional) - Only return active NPCs
    - npc_type: string (optional) - Filter by NPC type

    Returns list of NPCs.
    """
    active_only = request.args.get("active_only", "false").lower() == "true"
    npc_type_str = request.args.get("npc_type")

    npc_type = None
    if npc_type_str:
        npc_type = _parse_npc_type(npc_type_str)
        if npc_type is None:
            valid_types = [t.value for t in NPCType]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid npc_type filter. Valid values: {valid_types}",
                status_code=400,
            )

    npc_service = get_npc_service()

    npcs = npc_service.get_game_npcs(
        game_id=game_id,
        user_id=g.auth_user.user_id,
        active_only=active_only,
        npc_type=npc_type,
    )

    # Return different views based on user role
    if _is_dm(game_id, g.auth_user.user_id):
        return jsonify(NPCPresenter.collection(npcs)), 200
    else:
        return jsonify(NPCPresenter.player_collection(npcs)), 200


@npc_bp.get("/<int:game_id>/npc/<int:npc_id>")
@auth_required
def get_npc(game_id: int, npc_id: int):
    """
    Get a specific NPC by ID.

    Returns the NPC if the user has access.
    """
    npc_service = get_npc_service()

    npc = npc_service.get_npc(
        npc_id=npc_id,
        user_id=g.auth_user.user_id,
    )

    if not npc:
        return error_response(
            "NPC_NOT_FOUND",
            "NPC not found or not accessible",
            status_code=404,
        )

    if npc.game_id != game_id:
        return error_response(
            "NPC_NOT_FOUND",
            "NPC not found in this game",
            status_code=404,
        )

    # Return different views based on user role
    if _is_dm(game_id, g.auth_user.user_id):
        return jsonify(NPCPresenter.public(npc)), 200
    else:
        return jsonify(NPCPresenter.player_view(npc)), 200


@npc_bp.put("/<int:game_id>/npc/<int:npc_id>")
@auth_required
def update_npc(game_id: int, npc_id: int):
    """
    Update an NPC's data.

    Only the DM can update NPCs.

    Request body (all fields optional):
    {
        "name": "New Name",
        "npc_type": "ENEMY",
        "status": "DEFEATED",
        "description": "New description",
        "stats": { ... },
        "data": { ... }
    }

    Returns the updated NPC.
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    npc_type_str = data.get("npc_type")
    status_str = data.get("status")
    description = data.get("description")
    stats = data.get("stats")
    npc_data = data.get("data")

    if name is not None and (not name or not name.strip()):
        return error_response(
            "VALIDATION_ERROR",
            "NPC name cannot be empty",
            status_code=400,
        )

    npc_type = None
    if npc_type_str:
        npc_type = _parse_npc_type(npc_type_str)
        if npc_type is None:
            valid_types = [t.value for t in NPCType]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid npc_type. Valid values: {valid_types}",
                status_code=400,
            )

    status = None
    if status_str:
        status = _parse_npc_status(status_str)
        if status is None:
            valid_statuses = [s.value for s in NPCStatus]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid status. Valid values: {valid_statuses}",
                status_code=400,
            )

    npc_service = get_npc_service()

    try:
        # First verify the NPC belongs to this game
        npc = npc_service.get_npc(npc_id, g.auth_user.user_id)
        if not npc or npc.game_id != game_id:
            return error_response(
                "NPC_NOT_FOUND",
                "NPC not found in this game",
                status_code=404,
            )

        updated_npc = npc_service.update_npc(
            npc_id=npc_id,
            dm_user_id=g.auth_user.user_id,
            name=name.strip() if name else None,
            npc_type=npc_type,
            status=status,
            description=description,
            stats=stats,
            data=npc_data,
        )
        db.get_session().commit()
        return jsonify(NPCPresenter.public(updated_npc)), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("NPC_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@npc_bp.delete("/<int:game_id>/npc/<int:npc_id>")
@auth_required
def delete_npc(game_id: int, npc_id: int):
    """
    Delete an NPC.

    Only the DM can delete NPCs.

    Returns 204 No Content on success.
    """
    npc_service = get_npc_service()

    try:
        # First verify the NPC belongs to this game
        npc = npc_service.get_npc(npc_id, g.auth_user.user_id)
        if not npc or npc.game_id != game_id:
            return error_response(
                "NPC_NOT_FOUND",
                "NPC not found in this game",
                status_code=404,
            )

        npc_service.delete_npc(
            npc_id=npc_id,
            dm_user_id=g.auth_user.user_id,
        )
        db.get_session().commit()
        return "", 204
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("NPC_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

