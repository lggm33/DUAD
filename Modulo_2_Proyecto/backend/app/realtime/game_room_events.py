"""
Game room event handlers for SocketIO.

Handles joining and leaving game rooms for real-time updates.
"""

import logging
from flask import request
from flask_socketio import emit, join_room, leave_room

from app.extensions import db
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameMembershipStatus

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
                membership = membership_repo.get_game_membership_by_game_id_and_user_id(
                    game_id, user["user_id"]
                )

                if not membership or membership.status != GameMembershipStatus.ACTIVE:
                    emit("error", {"code": "NOT_MEMBER", "message": "Not a member of this game"})
                    return

                if user.get("game_id"):
                    leave_room(f"game_{user['game_id']}")

                join_room(f"game_{game_id}")
                user["game_id"] = game_id

                emit("joined_game", {"game_id": game_id})

                display_name = user.get("name") or user.get("username")
                broadcast_system_message(game_id, f"{display_name} joined the chat")

        except Exception as e:
            logger.error(f"[SocketIO] Error joining game: {e}")
            emit("error", {"code": "JOIN_FAILED", "message": "Failed to join game"})

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
                user["active_encounter_id"] = None
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
                user["active_encounter_id"] = None
        except Exception as e:
            logger.error(f"[SocketIO] Error in leave_game: {e}")
            leave_room(f"game_{game_id}")
            user["game_id"] = None

