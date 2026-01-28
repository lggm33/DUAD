"""
NPC endpoints for Non-Player Character management.

Only the DM can create, update, and delete NPCs.
All game members can view NPCs.
"""

from flask import Blueprint, request, jsonify, g


from app.extensions import db

from app.domain.npcs.npc_repository import NPCRepository
from app.domain.npcs.npc_service import NPCService
from app.domain.npcs.models import NPCType, NPCStatus
from app.domain.npcs.exceptions import (
    NPCNotFoundError,
    NPCAccessDeniedError,
    NPCValidationError,
    NPCStateError,
)
from app.domain.games.exceptions import GameNotFoundError
from app.domain.characters.character_repository import CharacterRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository

from app.presentation.npcs.presenters import NPCPresenter
from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response


npc_bp = Blueprint("npc", __name__, url_prefix="/api/v1/game")

def get_npc_service() -> NPCService:
    """
    Create and configure the NPC service with all dependencies.
    
    Returns:
        Configured NPCService instance
    """
    session = db.get_session()
    npc_repo = NPCRepository(session)
    character_repo = CharacterRepository(session)
    game_repo = GameRepository(session)
    membership_repo = GameMembershipRepository(session)
    return NPCService(npc_repo, character_repo, game_repo, membership_repo)


# ============================================================================
# ENDPOINTS
# ============================================================================

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

    Returns:
        201: Success with the created NPC
        400: Validation error
        403: Forbidden (not DM)
        404: Game not found
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    if not name or not name.strip():
        return error_response(
            "VALIDATION_ERROR",
            "NPC name is required",
            status_code=400,
        )

    npc_type_str = data.get("npc_type", "NEUTRAL")
    npc_type = _parse_npc_type(npc_type_str)
    if npc_type is None:
        valid_types = [t.value for t in NPCType]
        return error_response(
            "VALIDATION_ERROR",
            f"Invalid npc_type. Valid values: {valid_types}",
            status_code=400,
        )

    service = get_npc_service()

    try:
        npc = service.create_npc(
            game_id=game_id,
            dm_user_id=g.auth_user.user_id,
            name=name.strip(),
            npc_type=npc_type,
            description=data.get("description"),
            stats=data.get("stats", {}),
            data=data.get("data", {}),
        )
        return jsonify(NPCPresenter.public(npc)), 201

    except GameNotFoundError as e:
        return error_response("GAME_NOT_FOUND", str(e), status_code=404)
    except NPCAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except NPCValidationError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@npc_bp.get("/<int:game_id>/npcs")
@auth_required
def get_game_npcs(game_id: int):
    """
    Get all NPCs in a game.

    Query params:
    - active_only: bool (optional) - Only return active NPCs
    - npc_type: string (optional) - Filter by NPC type

    Returns:
        200: List of NPCs
        403: Forbidden (not a member)
        404: Game not found
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

    service = get_npc_service()

    try:
        npcs = service.get_game_npcs(
            game_id=game_id,
            user_id=g.auth_user.user_id,
            active_only=active_only,
            npc_type=npc_type,
        )
        # The service already filters data based on user membership/role
        # We use the collection presenter which uses public view
        return jsonify(NPCPresenter.collection(npcs)), 200

    except NPCAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except GameNotFoundError as e:
        return error_response("GAME_NOT_FOUND", str(e), status_code=404)


@npc_bp.get("/<int:game_id>/npc/<int:npc_id>")
@auth_required
def get_npc(game_id: int, npc_id: int):
    """
    Get a specific NPC by ID.

    Returns:
        200: The NPC
        403: Forbidden (not a member)
        404: NPC not found
    """
    service = get_npc_service()

    try:
        npc = service.get_npc(
            npc_id=npc_id,
            game_id=game_id,
            user_id=g.auth_user.user_id,
        )
        return jsonify(NPCPresenter.public(npc)), 200

    except NPCNotFoundError as e:
        return error_response("NPC_NOT_FOUND", str(e), status_code=404)
    except NPCAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


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

    Returns:
        200: Success with the updated NPC
        400: Validation error
        403: Forbidden (not DM)
        404: NPC not found
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    if name is not None and not name.strip():
        return error_response(
            "VALIDATION_ERROR",
            "NPC name cannot be empty",
            status_code=400,
        )

    npc_type = None
    if data.get("npc_type"):
        npc_type = _parse_npc_type(data.get("npc_type"))
        if npc_type is None:
            valid_types = [t.value for t in NPCType]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid npc_type. Valid values: {valid_types}",
                status_code=400,
            )

    status = None
    if data.get("status"):
        status = _parse_npc_status(data.get("status"))
        if status is None:
            valid_statuses = [s.value for s in NPCStatus]
            return error_response(
                "VALIDATION_ERROR",
                f"Invalid status. Valid values: {valid_statuses}",
                status_code=400,
            )

    service = get_npc_service()

    try:
        updated_npc = service.update_npc(
            npc_id=npc_id,
            game_id=game_id,
            dm_user_id=g.auth_user.user_id,
            name=name.strip() if name else None,
            npc_type=npc_type,
            status=status,
            description=data.get("description"),
            stats=data.get("stats"),
            data=data.get("data"),
        )
        return jsonify(NPCPresenter.public(updated_npc)), 200

    except NPCNotFoundError as e:
        return error_response("NPC_NOT_FOUND", str(e), status_code=404)
    except NPCAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except NPCValidationError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@npc_bp.delete("/<int:game_id>/npc/<int:npc_id>")
@auth_required
def delete_npc(game_id: int, npc_id: int):
    """
    Delete an NPC.

    Only the DM can delete NPCs.

    Returns:
        204: No Content on success
        403: Forbidden (not DM)
        404: NPC not found
    """
    service = get_npc_service()

    try:
        service.delete_npc(
            npc_id=npc_id,
            game_id=game_id,
            dm_user_id=g.auth_user.user_id,
        )
        return "", 204

    except NPCNotFoundError as e:
        return error_response("NPC_NOT_FOUND", str(e), status_code=404)
    except NPCAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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
