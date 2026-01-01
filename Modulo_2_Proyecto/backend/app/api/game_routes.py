from flask import Blueprint, request, jsonify, g
from app.presentation.common.auth import auth_required, roles_required
from app.presentation.common.errors import error_response
from app.domain.games.game_service import GameService
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameRoleInGame, GameMembershipStatus
from app.domain.games.schemas.validators import RulesValidationError
from app.domain.users.user_repository import UserRepository
from app.domain.users.models import UserRole
from app.domain.chat.chat_repository import ChatRepository
from app.domain.chat.chat_service import ChatService
from app.presentation.games.presenters import GamePresenter
from app.presentation.games.ruleset_presenters import GameRulesPresenter
from app.extensions import db

game_bp = Blueprint("game", __name__, url_prefix="/api/v1/game")

def get_game_service() -> GameService:
    session = db.get_session()
    game_repo = GameRepository(session)
    game_invites_repo = GameInvitesRepository(session)
    game_membership_repo = GameMembershipRepository(session)
    user_repo = UserRepository(session)
    return GameService(game_repo, game_invites_repo, game_membership_repo, user_repo)

@game_bp.post("/create")
@roles_required("ADMIN", "USER")
def create_game():
    data = request.get_json()
    print(data)
    if not data or "name" not in data or "dm_user_id" not in data:
        return error_response("VALIDATION_ERROR", "Name and DM user ID are required", status_code=400)

    game_service = get_game_service()
    try:
        create_game_result = game_service.create_game(data["name"], int(data["dm_user_id"]))
        return jsonify(GamePresenter.public(create_game_result)), 201
    except ValueError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@game_bp.post("/join")
@auth_required
def join_game():
    data = request.get_json()
    if not data or "game_id" not in data or "user_id" not in data:
        return error_response("VALIDATION_ERROR", "Game ID and user ID are required", status_code=400)

    game_service = get_game_service()
    try:
        membership = game_service.join_game(int(data["game_id"]), int(data["user_id"]))
        return jsonify(GamePresenter.game_only(membership.game)), 200
    except ValueError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@game_bp.post("/join-by-code")
@auth_required
def join_game_by_code():
    data = request.get_json()
    if not data or "invite_code" not in data:
        return error_response("VALIDATION_ERROR", "Invite code is required", status_code=400)

    game_service = get_game_service()
    try:
        result = game_service.join_game_by_code(data["invite_code"], g.auth_user.user_id)
        return jsonify(GamePresenter.game_only(result["game"])), 200
    except ValueError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@game_bp.post("/leave")
@auth_required
def leave_game():
    data = request.get_json()
    if not data or "game_id" not in data or "user_id" not in data:
        return error_response("VALIDATION_ERROR", "Game ID and user ID are required", status_code=400)

    game_service = get_game_service()
    try:
        leave_game_result = game_service.leave_game(int(data["game_id"]), int(data["user_id"]))
        return jsonify({"success": leave_game_result}), 200
    except ValueError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@game_bp.post("/kick")
@auth_required
def kick_user_from_game():
    data = request.get_json()
    if not data or "game_id" not in data or "user_id" not in data:
        return error_response("VALIDATION_ERROR", "Game ID and user ID are required", status_code=400)

    game_service = get_game_service()
    try:
        game_service.kick_user_from_game(int(data["game_id"]), int(data["user_id"]), g.auth_user)
        return jsonify(True), 200
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

@game_bp.get("/list-all")
@auth_required
def list_all_games():
    game_service = get_game_service()
    games = game_service.get_games(g.auth_user)
    return jsonify(GamePresenter.collection(games)), 200

@game_bp.get("/<int:game_id>")
@auth_required
def get_game_by_id(game_id: int):
    game_service = get_game_service()
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("GAME_NOT_FOUND", "Game not found", status_code=404)
        return jsonify(GamePresenter.game_only(game)), 200
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

@game_bp.get("/<int:game_id>/members")
@auth_required
def get_game_members(game_id: int):
    game_service = get_game_service()
    try:
        members = game_service.get_game_members(game_id, g.auth_user)
        return jsonify(GamePresenter.members_collection(members)), 200
    except ValueError as e:
        if "not found" in str(e).lower():
            return error_response("GAME_NOT_FOUND", str(e), status_code=404)
        return error_response("FORBIDDEN", str(e), status_code=403)


@game_bp.get("/<int:game_id>/messages")
@auth_required
def get_game_messages(game_id: int):
    """Get chat message history for a game."""
    # First verify user has access to this game
    game_service = get_game_service()
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("GAME_NOT_FOUND", "Game not found", status_code=404)
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

    # Get message history
    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 100)  # Cap at 100 messages

    session = db.get_session()
    chat_repo = ChatRepository(session)
    chat_service = ChatService(chat_repo)

    messages = chat_service.get_history(game_id, limit)
    messages_data = [chat_service.message_to_dict(msg) for msg in messages]

    return jsonify(messages_data), 200


# =============================================================================
# Rules Management Endpoints
# =============================================================================


def _get_game_membership(game_service: GameService, game_id: int, user_id: int):
    """Helper to get membership repository and check membership."""
    session = db.get_session()
    membership_repo = GameMembershipRepository(session)
    return membership_repo.get_game_membership_by_game_id_and_user_id(game_id, user_id)


@game_bp.get("/<int:game_id>/rules")
@auth_required
def get_game_rules(game_id: int):
    """
    Get effective rules for a game.
    
    Returns the merged rules (template base_rules + custom_rules).
    Accessible by any active member of the game.
    """
    game_service = get_game_service()
    
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("GAME_NOT_FOUND", "Game not found", status_code=404)
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    
    effective_rules = game_service.get_game_effective_rules(game)
    
    return jsonify(GameRulesPresenter.effective_rules(game, effective_rules)), 200


@game_bp.put("/<int:game_id>/rules")
@auth_required
def update_game_rules(game_id: int):
    """
    Update custom_rules for a game.
    
    Only the DM of the game can update the rules.
    
    Request body:
    {
        "custom_rules": { ... }  // Partial rules to override template
    }
    """
    game_service = get_game_service()
    
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("GAME_NOT_FOUND", "Game not found", status_code=404)
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    
    # Check if user is DM or ADMIN
    is_admin = g.auth_user.role == UserRole.ADMIN.value
    is_dm = game.dm_user_id == g.auth_user.user_id
    
    if not is_admin and not is_dm:
        # Additional check via membership
        membership = _get_game_membership(game_service, game_id, g.auth_user.user_id)
        if membership is None or membership.role_in_game != GameRoleInGame.DM:
            return error_response(
                "FORBIDDEN",
                "Only the DM can update game rules",
                status_code=403,
            )
    
    data = request.get_json()
    if data is None:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )
    
    custom_rules = data.get("custom_rules")
    
    try:
        game_service.set_game_custom_rules(game, custom_rules)
        db.get_session().commit()
    except RulesValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            e.message,
            details=e.errors if e.errors else None,
            status_code=400,
        )
    
    effective_rules = game_service.get_game_effective_rules(game)
    
    return jsonify(GameRulesPresenter.effective_rules(game, effective_rules)), 200
