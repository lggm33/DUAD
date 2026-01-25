"""
Game room event handlers for SocketIO.

Handles joining and leaving game rooms for real-time updates.
"""

import logging
from flask import request
from flask_socketio import emit, join_room, leave_room

from app.extensions import db
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.game_repository import GameRepository
from app.domain.games.models import GameMembershipStatus, GameRoleInGame

logger = logging.getLogger(__name__)


def register_game_room_events(socketio, app, shared_state, helpers):
    """Register game room-related SocketIO events."""

    authenticated_users = shared_state["authenticated_users"]
    broadcast_system_message = helpers["broadcast_system_message"]
    get_user_or_error = helpers["get_user_or_error"]

    @socketio.on("join_game")
    def handle_join_game(data):
        """Join a game room for real-time updates."""
        user = get_user_or_error()
        if not user:
            return

        game_id = data.get("game_id")
        if not game_id:
            emit("error", {"code": "INVALID_DATA", "message": "game_id is required"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                membership_repo = GameMembershipRepository(session)
                game_repo = GameRepository(session)
                
                membership = membership_repo.get_game_membership_by_game_id_and_user_id(
                    game_id, user["user_id"]
                )

                if not membership or membership.status != GameMembershipStatus.ACTIVE:
                    emit("error", {"code": "NOT_MEMBER", "message": "Not a member of this game"})
                    return

                if user.get("game_id"):
                    leave_room(f"game_{user['game_id']}")
                    leave_room(f"game_{user['game_id']}_dm")

                join_room(f"game_{game_id}")
                
                # If user is DM, also join the DM-only room for private dice rolls
                if membership.role_in_game == GameRoleInGame.DM:
                    join_room(f"game_{game_id}_dm")
                    user["is_dm"] = True
                else:
                    user["is_dm"] = False

                user["game_id"] = game_id

                emit("joined_game", {"game_id": game_id})

                display_name = user.get("name") or user.get("username")
                broadcast_system_message(game_id, f"{display_name} joined the chat")
                
                # Send current turn state to the joining user
                game = game_repo.get_game_by_id(game_id)
                if game and game.current_turn_user_id:
                    emit("turn_update", {
                        "user_id": game.current_turn_user_id,
                        "character_name": game.current_turn_character_name,
                        "set_by": None  # Historical info not stored
                    })

        except Exception as e:
            logger.error(f"[SocketIO] Error joining game: {e}")
            emit("error", {"code": "JOIN_FAILED", "message": "Failed to join game"})

    @socketio.on("set_turn")
    def handle_set_turn(data):
        """Set the active turn (DM only)."""
        user = get_user_or_error()
        if not user or not user.get("is_dm"):
            emit("error", {"code": "FORBIDDEN", "message": "Only DM can set turns"})
            return

        game_id = data.get("game_id")
        target_user_id = data.get("user_id")
        character_name = data.get("character_name")

        if not game_id or not target_user_id:
            emit("error", {"code": "INVALID_DATA", "message": "game_id and user_id are required"})
            return

        try:
            # Convert to integers (frontend sends as strings)
            try:
                game_id = int(game_id)
                target_user_id = int(target_user_id)
            except (ValueError, TypeError) as e:
                emit("error", {"code": "INVALID_DATA", "message": "Invalid game_id or user_id format"})
                return
            
            with app.app_context():
                session = db.get_session()
                game_repo = GameRepository(session)
                game = game_repo.get_game_by_id(game_id)
                
                if not game:
                    emit("error", {"code": "GAME_NOT_FOUND", "message": "Game not found"})
                    return
                
                # Persist turn state to database
                game.current_turn_user_id = target_user_id
                game.current_turn_character_name = character_name
                session.commit()
                
                logger.info(f"[SocketIO] Turn set to user {target_user_id} in game {game_id}")

            # Broadcast turn update to everyone
            emit("turn_update", {
                "user_id": target_user_id,
                "character_name": character_name,
                "set_by": user["user_id"]
            }, room=f"game_{game_id}")
            
        except Exception as e:
            logger.error(f"[SocketIO] Error setting turn: {e}")
            emit("error", {"code": "SET_TURN_FAILED", "message": "Failed to set turn"})

    @socketio.on("clear_turn")
    def handle_clear_turn(data):
        """Clear the active turn (DM only)."""
        user = get_user_or_error()
        if not user or not user.get("is_dm"):
            emit("error", {"code": "FORBIDDEN", "message": "Only DM can clear turns"})
            return

        game_id = data.get("game_id")
        if not game_id:
            emit("error", {"code": "INVALID_DATA", "message": "game_id is required"})
            return

        try:
            # Convert to integer (frontend sends as string)
            try:
                game_id = int(game_id)
            except (ValueError, TypeError) as e:
                emit("error", {"code": "INVALID_DATA", "message": "Invalid game_id format"})
                return
            
            with app.app_context():
                session = db.get_session()
                game_repo = GameRepository(session)
                game = game_repo.get_game_by_id(game_id)
                
                if not game:
                    emit("error", {"code": "GAME_NOT_FOUND", "message": "Game not found"})
                    return
                
                # Clear turn state from database
                game.current_turn_user_id = None
                game.current_turn_character_name = None
                session.commit()
                
                logger.info(f"[SocketIO] Turn cleared in game {game_id}")

            # Broadcast turn clear to everyone
            emit("turn_update", {"user_id": None, "character_name": None}, room=f"game_{game_id}")
            
        except Exception as e:
            logger.error(f"[SocketIO] Error clearing turn: {e}")
            emit("error", {"code": "CLEAR_TURN_FAILED", "message": "Failed to clear turn"})

    @socketio.on("leave_chat")
    def handle_leave_chat(data):
        """Leave the chat room."""
        user = authenticated_users.get(request.sid)
        if not user:
            return

        game_id = data.get("game_id") or user.get("game_id")
        if not game_id:
            return

        try:
            with app.app_context():
                display_name = user.get("name") or user.get("username")
                broadcast_system_message(game_id, f"{display_name} left the chat")
                leave_room(f"game_{game_id}")
                user["game_id"] = None
        except Exception as e:
            logger.error(f"[SocketIO] Error in leave_chat: {e}")
            leave_room(f"game_{game_id}")
            user["game_id"] = None

    @socketio.on("leave_game")
    def handle_leave_game(data):
        """Leave the game entirely."""
        user = authenticated_users.get(request.sid)
        if not user:
            return

        game_id = data.get("game_id") or user.get("game_id")
        if not game_id:
            return

        try:
            with app.app_context():
                display_name = user.get("name") or user.get("username")
                broadcast_system_message(game_id, f"{display_name} left the game")
                leave_room(f"game_{game_id}")
                user["game_id"] = None
        except Exception as e:
            logger.error(f"[SocketIO] Error in leave_game: {e}")
            leave_room(f"game_{game_id}")
            user["game_id"] = None

