from flask import Blueprint, request, jsonify, g
from app.presentation.common.auth import auth_required, roles_required
from app.presentation.common.errors import error_response
from app.domain.games.game_service import GameService
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.users.user_repository import UserRepository
from app.presentation.games.presenters import GamePresenter
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
@roles_required(["ADMIN", "PLAYER"])
def create_game():
    data = request.get_json()
    if not data or "name" not in data or "dm_user_id" not in data:
        return error_response("VALIDATION_ERROR", "Name and DM user ID are required", status_code=400)

    game_service = get_game_service()
    try:
        create_game_result = game_service.create_game(data["name"], data["dm_user_id"])
        return jsonify(GamePresenter.public(create_game_result["game"])), 201
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
        join_game_result = game_service.join_game(data["game_id"], data["user_id"])
        return jsonify(GamePresenter.public(join_game_result["game"])), 200
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
        leave_game_result = game_service.leave_game(data["game_id"], data["user_id"])
        return jsonify(GamePresenter.public(leave_game_result["game"])), 200
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
        game_service.kick_user_from_game(data["game_id"], data["user_id"], g.auth_user)
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
        return jsonify(GamePresenter.public(game)), 200
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


