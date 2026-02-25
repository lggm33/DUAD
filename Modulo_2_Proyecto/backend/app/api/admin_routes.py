from typing import Optional
from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.ruleset_repository import RulesetRepository
from app.domain.games.game_service import GameService
from app.domain.users.user_repository import UserRepository
from app.presentation.common.auth import roles_required
from app.presentation.common.errors import error_response
from app.domain.games.exceptions import GameNotFoundError, GameMembershipError

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")

def get_game_service() -> GameService:
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

@admin_bp.get("/games")
@roles_required("ADMIN")
def list_all_games():
    status = request.args.get("status")
    user_id = request.args.get("user_id", type=int)
    search = request.args.get("search")
    
    game_service = get_game_service()
    games = game_service.admin_list_games_with_filters(
        status=status,
        user_id=user_id,
        search=search
    )
    return jsonify({"games": games, "total": len(games)}), 200

@admin_bp.post("/games/<int:game_id>/end")
@roles_required("ADMIN")
def end_game(game_id: int):
    game_service = get_game_service()
    try:
        game_service.admin_end_game(game_id)
        return jsonify({"success": True}), 200
    except GameNotFoundError as e:
        return error_response("NOT_FOUND", str(e), status_code=404)

@admin_bp.post("/games/<int:game_id>/kick-member")
@roles_required("ADMIN")
def kick_member(game_id: int):
    data = request.get_json()
    if not data or "user_id" not in data:
        return error_response("VALIDATION_ERROR", "user_id is required", status_code=400)
    
    user_id = data["user_id"]
    game_service = get_game_service()
    try:
        result = game_service.admin_kick_member(game_id, user_id)
        return jsonify(result), 200
    except GameMembershipError as e:
        return error_response("VALIDATION_ERROR", str(e), status_code=400)

@admin_bp.get("/users")
@roles_required("ADMIN")
def list_users():
    game_service = get_game_service()
    users = game_service.admin_list_users()
    return jsonify({"users": users}), 200
