"""
Game API endpoints.

Provides REST API for game management including:
- Game CRUD operations
- Game membership (join, leave, kick)
- Game messages and chat
- Game rules management
"""
from typing import Optional

from flask import Blueprint, request, jsonify, g

from app.extensions import db

from app.domain.games.game_repository import GameRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.ruleset_repository import RulesetRepository
from app.domain.games.game_service import GameService
from app.domain.games.exceptions import (
    GameNotFoundError,
    GameAccessDeniedError,
    GameValidationError,
    GameStateError,
    GameInviteError,
    GameMembershipError,
    RulesetNotFoundError,
    RulesetAccessDeniedError,
)
from app.domain.games.schemas.validators import RulesValidationError
from app.domain.users.user_repository import UserRepository
from app.domain.chat.chat_repository import ChatRepository
from app.domain.chat.chat_service import ChatService

from app.presentation.games.presenters import GamePresenter
from app.presentation.games.ruleset_presenters import GameRulesPresenter

from app.presentation.common.auth import auth_required, roles_required
from app.presentation.common.errors import error_response

game_bp = Blueprint("game", __name__, url_prefix="/api/v1/game")


def get_game_service() -> GameService:
    """
    Create and configure the game service with all dependencies.
    
    This factory function instantiates all required repositories and
    utilities needed by the service.
    
    Note: Session is NOT passed to services. Transactions are handled
    automatically by Flask's request teardown.
    
    Returns:
        Configured GameService instance
    """
    session = db.get_session()
    
    game_repo = GameRepository(session)
    game_invites_repo = GameInvitesRepository(session)
    game_membership_repo = GameMembershipRepository(session)
    user_repo = UserRepository(session)
    ruleset_repo = RulesetRepository(session)
    
    return GameService(
        game_repo, 
        game_invites_repo, 
        game_membership_repo, 
        user_repo, 
        ruleset_repo
    )


def get_chat_service() -> ChatService:
    """
    Create and configure the chat service with all dependencies.
    
    Returns:
        Configured ChatService instance
    """
    session = db.get_session()
    chat_repo = ChatRepository(session)
    return ChatService(chat_repo)


# ============================================================================
# ENDPOINTS - GAME CRUD
# ============================================================================

@game_bp.post("/create")
@roles_required("ADMIN", "USER")
def create_game():
    """
    Create a new game with ruleset configuration.
    
    Request body:
    {
        "name": "Game Name",
        "dm_user_id": 1,
        "ruleset_template_id": 1,  
        "custom_rules": { ... } | null   
    }
    
    Returns:
        201: Game created successfully with invite code
        400: Validation error (missing fields, invalid rules)
        403: Forbidden (no access to ruleset template)
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    required_fields = ["name", "dm_user_id", "ruleset_template_id"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return error_response(
            "VALIDATION_ERROR",
            f"Missing required fields: {', '.join(missing_fields)}",
            status_code=400,
        )

    game_service = get_game_service()
    
    try:
        create_game_result = game_service.create_game(
            name=data["name"],
            dm_user_id=int(data["dm_user_id"]),
            ruleset_template_id=int(data["ruleset_template_id"]),
            custom_rules=data.get("custom_rules"),
        )
        return jsonify(GamePresenter.public(create_game_result)), 201
        
    except RulesValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            e.message,
            details=e.errors if e.errors else None,
            status_code=400,
        )
    except RulesetNotFoundError as e:
        return error_response("NOT_FOUND", str(e), status_code=404)
    except RulesetAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except GameValidationError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@game_bp.post("/join")
@auth_required
def join_game():
    """
    Join a game as a player.
    
    Request body:
    {
        "game_id": 1,
        "user_id": 2
    }
    
    Returns:
        200: Successfully joined game
        400: Validation error (missing fields, already member, kicked)
        404: Game not found
    """
    data = request.get_json()
    
    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )
    
    if "game_id" not in data or "user_id" not in data:
        return error_response(
            "VALIDATION_ERROR", 
            "Game ID and user ID are required", 
            status_code=400
        )

    game_service = get_game_service()
    
    try:
        membership = game_service.join_game(int(data["game_id"]), int(data["user_id"]))
        return jsonify(GamePresenter.game_only(membership.game)), 200
        
    except GameNotFoundError as e:
        return error_response("NOT_FOUND", str(e), status_code=404)
    except GameStateError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)
    except GameMembershipError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

@game_bp.post("/join-by-code")
@auth_required
def join_game_by_code():
    """
    Join a game using an invite code.
    
    Request body:
    {
        "invite_code": "abc123xyz"
    }
    
    Returns:
        200: Successfully joined game
        400: Invalid or expired invite code
    """
    data = request.get_json()
    
    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )
    
    if "invite_code" not in data:
        return error_response(
            "VALIDATION_ERROR", 
            "Invite code is required", 
            status_code=400
        )

    game_service = get_game_service()
    
    try:
        result = game_service.join_game_by_code(
            data["invite_code"], 
            g.auth_user.user_id
        )
        return jsonify(GamePresenter.game_only(result["game"])), 200
        
    except GameInviteError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)
    except GameStateError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)
    except GameMembershipError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@game_bp.post("/leave")
@auth_required
def leave_game():
    """
    Leave a game.
    
    Request body:
    {
        "game_id": 1,
        "user_id": 2
    }
    
    Returns:
        200: Successfully left game
        400: Not an active member
        404: Game not found
    """
    data = request.get_json()
    
    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )
    
    if "game_id" not in data or "user_id" not in data:
        return error_response(
            "VALIDATION_ERROR", 
            "Game ID and user ID are required", 
            status_code=400
        )

    game_service = get_game_service()
    
    try:
        leave_game_result = game_service.leave_game(
            int(data["game_id"]), 
            int(data["user_id"])
        )
        return jsonify({"success": leave_game_result}), 200
        
    except GameNotFoundError as e:
        return error_response("NOT_FOUND", str(e), status_code=404)
    except GameMembershipError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@game_bp.post("/kick")
@auth_required
def kick_user_from_game():
    """
    Kick a user from a game.
    
    Only DM or ADMIN can kick users.
    
    Request body:
    {
        "game_id": 1,
        "user_id": 2
    }
    
    Returns:
        200: User kicked successfully
        400: User not a member
        403: Not authorized to kick
    """
    data = request.get_json()
    
    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )
    
    if "game_id" not in data or "user_id" not in data:
        return error_response(
            "VALIDATION_ERROR", 
            "Game ID and user ID are required", 
            status_code=400
        )

    game_service = get_game_service()
    
    try:
        game_service.kick_user_from_game(
            int(data["game_id"]), 
            int(data["user_id"]), 
            g.auth_user
        )
        return jsonify({"success": True}), 200
        
    except GameMembershipError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

@game_bp.get("/list-all")
@auth_required
def list_all_games():
    """
    List all games accessible by the authenticated user.
    
    ADMIN users see all games.
    Regular users see only games they are/were members of.
    
    Returns:
        200: List of games with role and membership status
    """
    game_service = get_game_service()
    games = game_service.get_games(g.auth_user)
    return jsonify(GamePresenter.collection(games)), 200

@game_bp.get("/<int:game_id>")
@auth_required
def get_game_by_id(game_id: int):
    """
    Get a specific game by ID.
    
    User must be an active member or ADMIN.
    
    Returns:
        200: Game details
        403: Not a member of the game
        404: Game not found
    """
    game_service = get_game_service()
    
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("NOT_FOUND", "Game not found", status_code=404)
        return jsonify(GamePresenter.game_only(game)), 200
        
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

@game_bp.get("/<int:game_id>/members")
@auth_required
def get_game_members(game_id: int):
    """
    Get all members of a game.
    
    User must be an active member or ADMIN.
    
    Returns:
        200: List of game members with user information
        403: Not a member of the game
        404: Game not found
    """
    game_service = get_game_service()
    
    try:
        members = game_service.get_game_members(game_id, g.auth_user)
        return jsonify(GamePresenter.members_collection(members)), 200
        
    except GameNotFoundError as e:
        return error_response("NOT_FOUND", str(e), status_code=404)
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)



# ============================================================================
# ENDPOINTS - CHAT
# ============================================================================

@game_bp.get("/<int:game_id>/messages")
@auth_required
def get_game_messages(game_id: int):
    """
    Get chat message history for a game.
    
    Messages are filtered based on privacy rules:
    - System and regular messages: visible to all
    - DM's dice rolls: only visible to DM
    - Player's dice rolls: visible to player and DM
    
    Query params:
    - limit: Number of messages to retrieve (default: 50, max: 1000)
    
    Returns:
        200: List of chat messages
        403: Not a member of the game
        404: Game not found
    """
    game_service = get_game_service()
    
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("NOT_FOUND", "Game not found", status_code=404)
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)

    # Get message history with limit
    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 1000)

    chat_service = get_chat_service()
    messages = chat_service.get_history(game_id, limit)
    
    # Filter messages based on privacy rules (business logic in service)
    filtered_messages = chat_service.get_filtered_messages_for_user(
        messages=messages,
        user_id=g.auth_user.user_id,
        dm_user_id=game.dm_user_id
    )

    messages_data = [chat_service.message_to_dict(msg) for msg in filtered_messages]

    return jsonify(messages_data), 200



# ============================================================================
# ENDPOINTS - RULES MANAGEMENT
# ============================================================================

@game_bp.get("/<int:game_id>/rules")
@auth_required
def get_game_rules(game_id: int):
    """
    Get effective rules for a game.
    
    Returns the merged rules (template base_rules + custom_rules).
    Accessible by any active member of the game.
    
    Returns:
        200: Effective game rules
        403: Not a member of the game
        404: Game not found
    """
    game_service = get_game_service()
    
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("NOT_FOUND", "Game not found", status_code=404)
            
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    
    effective_rules = game_service.get_game_effective_rules(game)
    
    return jsonify(GameRulesPresenter.effective_rules(game, effective_rules)), 200


@game_bp.put("/<int:game_id>/rules")
@auth_required
def update_game_rules(game_id: int):
    """
    Update custom_rules for a game.
    
    Only the DM or ADMIN can update the rules.
    
    Request body:
    {
        "custom_rules": { ... }  // Partial rules to override template
    }
    
    Returns:
        200: Rules updated successfully
        400: Validation error (invalid rules)
        403: Not authorized (not DM or ADMIN)
        404: Game not found
    """
    game_service = get_game_service()
    
    try:
        game = game_service.get_game_by_id(game_id, g.auth_user)
        if not game:
            return error_response("NOT_FOUND", "Game not found", status_code=404)
            
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    
    # Verify user has DM permissions (business logic in service)
    try:
        game_service.verify_dm_permissions(game, g.auth_user)
    except GameAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    
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
        # No commit needed - Flask handles it automatically
        
    except RulesValidationError as e:
        return error_response(
            "VALIDATION_ERROR",
            e.message,
            details=e.errors if e.errors else None,
            status_code=400,
        )
    
    effective_rules = game_service.get_game_effective_rules(game)
    
    return jsonify(GameRulesPresenter.effective_rules(game, effective_rules)), 200
