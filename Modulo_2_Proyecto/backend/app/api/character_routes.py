"""
Character endpoints for player character management.
"""

from flask import Blueprint, request, jsonify, g

from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response
from app.presentation.characters.presenters import CharacterPresenter
from app.domain.characters.character_service import CharacterService
from app.domain.characters.character_repository import CharacterRepository
from app.domain.characters.models import CharacterStatus
from app.domain.games.game_repository import GameRepository
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.users.user_repository import UserRepository
from app.extensions import db
from app.realtime.character_events import CharacterEventEmitter


character_bp = Blueprint("character", __name__, url_prefix="/api/v1/game")


def get_character_service() -> CharacterService:
    session = db.get_session()
    character_repo = CharacterRepository(session)
    game_repo = GameRepository(session)
    membership_repo = GameMembershipRepository(session)
    return CharacterService(character_repo, game_repo, membership_repo)


@character_bp.post("/<int:game_id>/character")
@auth_required
def create_character(game_id: int):
    """
    Create a new character in the game.

    Request body:
    {
        "name": "Character Name",
        "data": { ... character data ... },
        "submit_for_approval": true/false (optional, default false)
    }

    If submit_for_approval is true and the game requires approval,
    the character will be created with PENDING_APPROVAL status.
    If the game doesn't require approval, it will be auto-approved.

    Returns 201 with the created character.
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    character_data = data.get("data", {})
    submit_for_approval = data.get("submit_for_approval", False)

    if not name or not name.strip():
        return error_response(
            "VALIDATION_ERROR",
            "Character name is required",
            status_code=400,
        )

    character_service = get_character_service()

    try:
        character = character_service.create_character(
            game_id=game_id,
            user_id=g.auth_user.user_id,
            name=name.strip(),
            data=character_data,
            submit_for_approval=submit_for_approval,
        )
        db.get_session().commit()

        if character.status == CharacterStatus.PENDING_APPROVAL:
            session = db.get_session()
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(g.auth_user.user_id)
            player_name = user.username if user else "Unknown"

            CharacterEventEmitter.emit_character_submitted(
                game_id=game_id,
                character_id=character.id,
                character_name=character.name,
                player_name=player_name,
                user_id=g.auth_user.user_id,
            )

        return jsonify(CharacterPresenter.public(character)), 201
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("NOT_FOUND", str(e), status_code=404)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@character_bp.get("/<int:game_id>/characters")
@auth_required
def get_game_characters(game_id: int):
    """
    Get all characters in a game visible to the current user.

    Query params:
    - include_pending: bool (optional, DM only) - Include pending approval characters
    - status: string (optional) - Filter by character status (APPROVED, DRAFT, etc.)

    Returns list of characters.
    """
    include_pending = request.args.get("include_pending", "false").lower() == "true"
    status_filter = request.args.get("status")

    character_service = get_character_service()

    try:
        characters = character_service.get_game_characters(
            game_id=game_id,
            user_id=g.auth_user.user_id,
            include_pending=include_pending,
        )

        # Apply status filter if provided
        if status_filter:
            status_filter = status_filter.upper()
            characters = [c for c in characters if c.status.value == status_filter]

        return jsonify(CharacterPresenter.collection(characters)), 200
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


@character_bp.get("/<int:game_id>/character/<int:character_id>")
@auth_required
def get_character(game_id: int, character_id: int):
    """
    Get a specific character by ID.

    Returns the character if the user has access.
    """
    character_service = get_character_service()

    character = character_service.get_character(
        character_id=character_id,
        user_id=g.auth_user.user_id,
    )

    if not character:
        return error_response(
            "CHARACTER_NOT_FOUND",
            "Character not found or not accessible",
            status_code=404,
        )

    if character.game_id != game_id:
        return error_response(
            "CHARACTER_NOT_FOUND",
            "Character not found in this game",
            status_code=404,
        )

    return jsonify(CharacterPresenter.public(character)), 200


@character_bp.put("/<int:game_id>/character/<int:character_id>")
@auth_required
def update_character(game_id: int, character_id: int):
    """
    Update a character's data.

    Only the owner can update, and only if the character is editable
    (DRAFT or REJECTED status).

    Request body:
    {
        "name": "New Name",  // optional
        "data": { ... },     // optional
        "submit_for_approval": true/false  // optional
    }

    Returns the updated character.
    """
    data = request.get_json()

    if not data:
        return error_response(
            "VALIDATION_ERROR",
            "Request body is required",
            status_code=400,
        )

    name = data.get("name")
    character_data = data.get("data")
    submit_for_approval = data.get("submit_for_approval", False)

    if name is not None and (not name or not name.strip()):
        return error_response(
            "VALIDATION_ERROR",
            "Character name cannot be empty",
            status_code=400,
        )

    character_service = get_character_service()

    try:
        # First verify the character belongs to this game
        character = character_service.get_character(character_id, g.auth_user.user_id)
        if not character or character.game_id != game_id:
            return error_response(
                "CHARACTER_NOT_FOUND",
                "Character not found in this game",
                status_code=404,
            )

        updated_character = character_service.update_character(
            character_id=character_id,
            user_id=g.auth_user.user_id,
            name=name.strip() if name else None,
            data=character_data,
            submit_for_approval=submit_for_approval,
        )
        db.get_session().commit()

        # Emit event if submitted for approval
        if submit_for_approval and updated_character.status == CharacterStatus.PENDING_APPROVAL:
            session = db.get_session()
            user_repo = UserRepository(session)
            user = user_repo.get_by_id(g.auth_user.user_id)
            player_name = user.username if user else "Unknown"

            CharacterEventEmitter.emit_character_submitted(
                game_id=game_id,
                character_id=updated_character.id,
                character_name=updated_character.name,
                player_name=player_name,
                user_id=g.auth_user.user_id,
            )
        return jsonify(CharacterPresenter.public(updated_character)), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
        if "cannot be edited" in error_msg or "only update your own" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@character_bp.post("/<int:game_id>/character/<int:character_id>/approve")
@auth_required
def approve_character(game_id: int, character_id: int):
    """
    DM approves a character.

    Only the DM of the game can approve characters.
    The character must be in PENDING_APPROVAL status.

    Request body (optional):
    {
        "feedback": "Great character!"
    }

    Returns the approved character.
    """
    data = request.get_json() or {}
    feedback = data.get("feedback")

    character_service = get_character_service()

    try:
        # First verify the character belongs to this game
        character = character_service.get_character(character_id, g.auth_user.user_id)
        if not character or character.game_id != game_id:
            return error_response(
                "CHARACTER_NOT_FOUND",
                "Character not found in this game",
                status_code=404,
            )

        approved_character = character_service.approve_character(
            character_id=character_id,
            dm_user_id=g.auth_user.user_id,
            feedback=feedback,
        )
        db.get_session().commit()

        CharacterEventEmitter.emit_character_approved(
            game_id=game_id,
            character_id=character_id,
            character_name=approved_character.name,
            user_id=approved_character.user_id,
            feedback=feedback,
        )

        return jsonify(CharacterPresenter.public(approved_character)), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@character_bp.post("/<int:game_id>/character/<int:character_id>/reject")
@auth_required
def reject_character(game_id: int, character_id: int):
    """
    DM rejects a character with feedback.

    Only the DM of the game can reject characters.
    The character must be in PENDING_APPROVAL status.
    Feedback is required.

    Request body:
    {
        "feedback": "Please adjust the stats..."
    }

    Returns the rejected character.
    """
    data = request.get_json()

    if not data or not data.get("feedback"):
        return error_response(
            "VALIDATION_ERROR",
            "Feedback is required when rejecting a character",
            status_code=400,
        )

    feedback = data["feedback"]

    character_service = get_character_service()

    try:
        # First verify the character belongs to this game
        character = character_service.get_character(character_id, g.auth_user.user_id)
        if not character or character.game_id != game_id:
            return error_response(
                "CHARACTER_NOT_FOUND",
                "Character not found in this game",
                status_code=404,
            )

        rejected_character = character_service.reject_character(
            character_id=character_id,
            dm_user_id=g.auth_user.user_id,
            feedback=feedback,
        )
        db.get_session().commit()

        CharacterEventEmitter.emit_character_rejected(
            game_id=game_id,
            character_id=character_id,
            character_name=rejected_character.name,
            user_id=rejected_character.user_id,
            feedback=feedback,
        )

        return jsonify(CharacterPresenter.public(rejected_character)), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@character_bp.get("/<int:game_id>/characters/pending")
@auth_required
def get_pending_characters(game_id: int):
    """
    Get characters pending approval (DM only).

    Only the DM of the game can view pending characters.

    Returns list of characters with PENDING_APPROVAL status.
    """
    character_service = get_character_service()

    try:
        characters = character_service.get_pending_characters(
            game_id=game_id,
            dm_user_id=g.auth_user.user_id,
        )
        return jsonify(CharacterPresenter.collection(characters)), 200
    except ValueError as e:
        error_msg = str(e).lower()
        if "only the dm" in error_msg:
            return error_response("FORBIDDEN", str(e), status_code=403)
        return error_response("VALIDATION_ERROR", str(e), status_code=400)


@character_bp.get("/<int:game_id>/my-character")
@auth_required
def get_my_character(game_id: int):
    """
    Get the current user's character in a game.

    Returns the user's character or 404 if they don't have one.
    """
    character_service = get_character_service()

    character = character_service.get_user_character_in_game(
        game_id=game_id,
        user_id=g.auth_user.user_id,
    )

    if not character:
        return error_response(
            "CHARACTER_NOT_FOUND",
            "You don't have a character in this game",
            status_code=404,
        )

    return jsonify(CharacterPresenter.public(character)), 200

