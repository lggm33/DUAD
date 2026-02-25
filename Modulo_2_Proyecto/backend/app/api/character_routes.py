"""
Character endpoints for player character management.
"""

from flask import Blueprint, request, jsonify, g

from app.presentation.common.auth import auth_required
from app.presentation.common.errors import error_response
from app.presentation.characters.presenters import CharacterPresenter
from app.domain.characters.character_service import CharacterService
from app.domain.characters.character_repository import CharacterRepository
from app.domain.characters.inventory_service import InventoryService
from app.domain.characters.exceptions import (
    CharacterNotFoundError,
    CharacterAccessDeniedError,
    CharacterNotEditableError,
    InventoryItemNotFoundError,
)
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
    user_repo = UserRepository(session)
    event_emitter = CharacterEventEmitter()
    return CharacterService(
        character_repo,
        game_repo,
        membership_repo,
        user_repo,
        event_emitter,
    )


def get_inventory_service() -> InventoryService:
    session = db.get_session()
    character_repo = CharacterRepository(session)
    return InventoryService(character_repo)


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

    if not data or not data.get("name"):
        return error_response(
            "VALIDATION_ERROR",
            "Name is required",
            status_code=400,
        )

    character_service = get_character_service()

    try:
        character = character_service.create_character(
            game_id=game_id,
            user_id=g.auth_user.user_id,
            name=data["name"],
            data=data.get("data", {}),
            submit_for_approval=data.get("submit_for_approval", False),
        )
        return jsonify(CharacterPresenter.public(character)), 201
    except CharacterNotFoundError as e:
        return error_response("NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except ValueError as e:
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
            status_filter=status_filter,
        )
        return jsonify(CharacterPresenter.collection(characters)), 200
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


@character_bp.get("/<int:game_id>/character/<int:character_id>")
@auth_required
def get_character(game_id: int, character_id: int):
    """
    Get a specific character by ID.

    Returns the character if the user has access.
    """
    character_service = get_character_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
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

        return jsonify(CharacterPresenter.public(character)), 200
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)


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
    if name is not None and not name.strip():
        return error_response(
            "VALIDATION_ERROR",
            "Character name cannot be empty",
            status_code=400,
        )

    character_service = get_character_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
        
        updated_character = character_service.update_character(
            character_id=character_id,
            user_id=g.auth_user.user_id,
            name=name.strip() if name else None,
            data=data.get("data"),
            submit_for_approval=data.get("submit_for_approval", False),
        )
        return jsonify(CharacterPresenter.public(updated_character)), 200
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except CharacterNotEditableError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except ValueError as e:
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
    character_service = get_character_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
        
        approved_character = character_service.approve_character(
            character_id=character_id,
            dm_user_id=g.auth_user.user_id,
            feedback=data.get("feedback"),
        )
        return jsonify(CharacterPresenter.public(approved_character)), 200
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except ValueError as e:
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

    character_service = get_character_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
        
        rejected_character = character_service.reject_character(
            character_id=character_id,
            dm_user_id=g.auth_user.user_id,
            feedback=data["feedback"],
        )
        return jsonify(CharacterPresenter.public(rejected_character)), 200
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except ValueError as e:
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
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


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


# ============================================================================
# INVENTORY ENDPOINTS
# ============================================================================

@character_bp.get("/<int:game_id>/character/<int:character_id>/inventory")
@auth_required
def get_character_inventory(game_id: int, character_id: int):
    """
    Get all inventory items for a character.

    Returns the inventory array from the character's data field.
    Only the character owner can access their inventory.
    """
    character_service = get_character_service()
    inventory_service = get_inventory_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
        inventory = inventory_service.get_inventory(character_id, g.auth_user.user_id)
        return jsonify({"inventory": inventory}), 200
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


@character_bp.post("/<int:game_id>/character/<int:character_id>/inventory")
@auth_required
def add_inventory_item(game_id: int, character_id: int):
    """
    Add a new item to the character's inventory.

    Request body:
    {
        "name": "Item Name",
        "description": "Item description",
        "quantity": 1
    }

    Returns the created item with its generated ID.
    """
    data = request.get_json()

    if not data or not data.get("name"):
        return error_response(
            "VALIDATION_ERROR",
            "Item name is required",
            status_code=400,
        )

    quantity = data.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1:
        return error_response(
            "VALIDATION_ERROR",
            "Quantity must be a positive integer",
            status_code=400,
        )

    character_service = get_character_service()
    inventory_service = get_inventory_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
        
        item = inventory_service.add_item(
            character_id=character_id,
            user_id=g.auth_user.user_id,
            name=data["name"],
            description=data.get("description", ""),
            quantity=quantity,
        )
        return jsonify({"item": item}), 201
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)


@character_bp.put("/<int:game_id>/character/<int:character_id>/inventory/<item_id>")
@auth_required
def update_inventory_item(game_id: int, character_id: int, item_id: str):
    """
    Update an existing inventory item.

    Request body:
    {
        "name": "Updated Name",  // optional
        "description": "Updated description",  // optional
        "quantity": 2  // optional
    }

    Returns the updated item.
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
            "Item name cannot be empty",
            status_code=400,
        )

    quantity = data.get("quantity")
    if quantity is not None and (not isinstance(quantity, int) or quantity < 1):
        return error_response(
            "VALIDATION_ERROR",
            "Quantity must be a positive integer",
            status_code=400,
        )

    character_service = get_character_service()
    inventory_service = get_inventory_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
        
        item = inventory_service.update_item(
            character_id=character_id,
            user_id=g.auth_user.user_id,
            item_id=item_id,
            name=name,
            description=data.get("description"),
            quantity=quantity,
        )
        return jsonify({"item": item}), 200
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except InventoryItemNotFoundError as e:
        return error_response("ITEM_NOT_FOUND", str(e), status_code=404)


@character_bp.delete("/<int:game_id>/character/<int:character_id>/inventory/<item_id>")
@auth_required
def delete_inventory_item(game_id: int, character_id: int, item_id: str):
    """
    Delete an item from the character's inventory.

    Returns 204 No Content on success.
    """
    character_service = get_character_service()
    inventory_service = get_inventory_service()

    try:
        character_service.verify_character_in_game(character_id, game_id)
        
        inventory_service.delete_item(
            character_id=character_id,
            user_id=g.auth_user.user_id,
            item_id=item_id,
        )
        return "", 204
    except CharacterNotFoundError as e:
        return error_response("CHARACTER_NOT_FOUND", str(e), status_code=404)
    except CharacterAccessDeniedError as e:
        return error_response("FORBIDDEN", str(e), status_code=403)
    except InventoryItemNotFoundError as e:
        return error_response("ITEM_NOT_FOUND", str(e), status_code=404)

