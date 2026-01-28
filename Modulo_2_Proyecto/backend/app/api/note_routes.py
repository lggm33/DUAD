from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.domain.notes.note_repository import NoteRepository
from app.domain.notes.note_service import NoteService
from app.domain.notes.models import NoteVisibility
from app.domain.notes.exceptions import (
    NoteNotFoundError,
    NoteAccessDeniedError,
    NoteValidationError
)
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.game_service import GameService
from app.domain.games.ruleset_repository import RulesetRepository
from app.domain.users.user_repository import UserRepository
from app.domain.games.game_invites_repository import GameInvitesRepository
from app.domain.games.exceptions import GameNotFoundError
from app.presentation.notes.presenters import NotePresenter
from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response

note_bp = Blueprint("note", __name__, url_prefix="/api/v1/notes")

def get_note_service() -> NoteService:
    session = db.get_session()
    note_repo = NoteRepository(session)
    game_repo = GameRepository(session)
    membership_repo = GameMembershipRepository(session)
    user_repo = UserRepository(session)
    ruleset_repo = RulesetRepository(session)
    invites_repo = GameInvitesRepository(session)
    
    game_service = GameService(
        game_repo,
        invites_repo,
        membership_repo,
        user_repo,
        ruleset_repo
    )
    
    return NoteService(note_repo, game_repo, membership_repo, game_service)

@note_bp.post("/<int:game_id>/note")
@auth_required
def create_note(game_id: int):
    data = request.get_json()
    if not data:
        return error_response("VALIDATION_ERROR", "Request body required", 400)
    
    title = data.get("title")
    content = data.get("content")
    visibility_str = data.get("visibility", "PRIVATE")
    
    try:
        visibility = NoteVisibility(visibility_str.upper())
    except (ValueError, AttributeError):
        return error_response("VALIDATION_ERROR", f"Invalid visibility. Valid values: {[v.value for v in NoteVisibility]}", 400)
    
    service = get_note_service()
    try:
        note = service.create_note(
            game_id=game_id,
            user_id=g.auth_user.user_id,
            title=title,
            content=content,
            visibility=visibility,
            auth_user=g.auth_user
        )
        return jsonify(NotePresenter.public(note)), 201
    except GameNotFoundError as e:
        return error_response("NOT_FOUND", str(e), 404)
    except NoteAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), 403)
    except NoteValidationError as e:
        return error_response("VALIDATION_ERROR", str(e), 400)

@note_bp.get("/<int:game_id>/notes")
@auth_required
def get_game_notes(game_id: int):
    service = get_note_service()
    try:
        notes = service.get_game_notes(game_id, g.auth_user)
        return jsonify({
            "shared": NotePresenter.collection(notes["shared"]),
            "private": NotePresenter.collection(notes["private"])
        }), 200
    except NoteAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), 403)

@note_bp.get("/<int:game_id>/note/<int:note_id>")
@auth_required
def get_note(game_id: int, note_id: int):
    service = get_note_service()
    try:
        note = service.get_note_by_id(note_id, game_id, g.auth_user)
        return jsonify(NotePresenter.public(note)), 200
    except NoteNotFoundError as e:
        return error_response("NOT_FOUND", str(e), 404)
    except NoteAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), 403)

@note_bp.put("/<int:game_id>/note/<int:note_id>")
@auth_required
def update_note(game_id: int, note_id: int):
    data = request.get_json()
    if not data:
        return error_response("VALIDATION_ERROR", "Request body required", 400)
    
    visibility = None
    if "visibility" in data:
        try:
            visibility = NoteVisibility(data["visibility"].upper())
        except (ValueError, AttributeError):
            return error_response("VALIDATION_ERROR", "Invalid visibility", 400)
            
    service = get_note_service()
    try:
        note = service.update_note(
            note_id=note_id,
            game_id=game_id,
            auth_user=g.auth_user,
            title=data.get("title"),
            content=data.get("content"),
            visibility=visibility
        )
        return jsonify(NotePresenter.public(note)), 200
    except NoteNotFoundError as e:
        return error_response("NOT_FOUND", str(e), 404)
    except NoteAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), 403)
    except NoteValidationError as e:
        return error_response("VALIDATION_ERROR", str(e), 400)

@note_bp.delete("/<int:game_id>/note/<int:note_id>")
@auth_required
def delete_note(game_id: int, note_id: int):
    service = get_note_service()
    try:
        service.delete_note(note_id, game_id, g.auth_user)
        return "", 204
    except NoteNotFoundError as e:
        return error_response("NOT_FOUND", str(e), 404)
    except NoteAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), 403)
