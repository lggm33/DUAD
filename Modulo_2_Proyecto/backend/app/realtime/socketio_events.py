"""
Flask-SocketIO event handlers for real-time communication.

This module handles WebSocket connections, authentication, and chat messages
using Flask-SocketIO's built-in room management.
"""

import logging
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect

from app.config import get_settings
from app.extensions import db
from app.utils.jwt_service import JwtService
from app.domain.users.user_repository import UserRepository
from app.domain.chat.chat_repository import ChatRepository
from app.domain.chat.chat_service import ChatService
from app.domain.games.game_membership_repository import GameMembershipRepository
from app.domain.games.models import GameMembershipStatus

logger = logging.getLogger(__name__)

# Store authenticated users by session id
# {sid: {"user_id": int, "username": str, "game_id": int | None}}
authenticated_users: dict[str, dict] = {}


def register_socketio_events(socketio, app):
    """Register all SocketIO event handlers."""

    @socketio.on("connect")
    def handle_connect(auth):
        """Handle new WebSocket connection with JWT authentication."""
        logger.info(f"[SocketIO] New connection attempt: {request.sid}")
        logger.info(f"[SocketIO] Auth: {auth}")

        if not auth or "token" not in auth:
            logger.warning(f"[SocketIO] Connection rejected: no token provided")
            return False  # Reject connection

        token = auth["token"]

        try:
            with app.app_context():
                settings = get_settings()
                jwt_service = JwtService(secret_key=settings.jwt_secret_key)
                payload = jwt_service.verify(token)
                user_id = int(payload["sub"])

                session = db.get_session()
                user_repo = UserRepository(session)
                user = user_repo.get_by_id(user_id)

                if not user:
                    logger.warning(f"[SocketIO] Connection rejected: user {user_id} not found")
                    return False

                # Store user info
                authenticated_users[request.sid] = {
                    "user_id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "game_id": None
                }

                logger.info(f"[SocketIO] User {user.username} (id={user.id}) connected")
                emit("auth_ok", {"user_id": user.id, "username": user.username, "name": user.name})

        except Exception as e:
            logger.error(f"[SocketIO] Auth failed: {e}")
            return False  # Reject connection

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        user = authenticated_users.pop(request.sid, None)
        if user:
            logger.info(f"[SocketIO] User {user['username']} disconnected")
            if user.get("game_id"):
                # Notify others in the game room
                emit(
                    "user_left",
                    {"user_id": user["user_id"], "username": user["username"], "name": user["name"]},
                    room=f"game_{user['game_id']}",
                )

    @socketio.on("join_game")
    def handle_join_game(data):
        """Join a game room for real-time updates."""
        user = authenticated_users.get(request.sid)
        if not user:
            emit("error", {"code": "NOT_AUTHENTICATED", "message": "Not authenticated"})
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

                # Leave previous game room if any
                if user.get("game_id"):
                    leave_room(f"game_{user['game_id']}")

                # Join new game room
                room_name = f"game_{game_id}"
                join_room(room_name)
                user["game_id"] = game_id

                logger.info(f"[SocketIO] User {user['username']} joined game {game_id}")

                # Notify others in the room
                emit(
                    "user_joined",
                    {"user_id": user["user_id"], "username": user["username"], "name": user["name"]},
                    room=room_name,
                    include_self=False,
                )

                emit("joined_game", {"game_id": game_id})

        except Exception as e:
            logger.error(f"[SocketIO] Error joining game: {e}")
            emit("error", {"code": "JOIN_FAILED", "message": "Failed to join game"})

    @socketio.on("leave_game")
    def handle_leave_game(data):
        """Leave the current game room."""
        user = authenticated_users.get(request.sid)
        if not user:
            return

        game_id = data.get("game_id") or user.get("game_id")
        if not game_id:
            return

        room_name = f"game_{game_id}"
        leave_room(room_name)

        # Notify others
        emit(
            "user_left",
            {"user_id": user["user_id"], "username": user["username"], "name": user["name"]},
            room=room_name,
        )

        user["game_id"] = None
        logger.info(f"[SocketIO] User {user['username']} left game {game_id}")

    @socketio.on("chat_message")
    def handle_chat_message(data):
        """Handle incoming chat message."""
        user = authenticated_users.get(request.sid)
        if not user:
            emit("error", {"code": "NOT_AUTHENTICATED", "message": "Not authenticated"})
            return

        game_id = data.get("game_id")
        content = data.get("content", "").strip()

        if not game_id or not content:
            emit("error", {"code": "INVALID_DATA", "message": "game_id and content are required"})
            return

        if user.get("game_id") != game_id:
            emit("error", {"code": "NOT_IN_GAME", "message": "You are not in this game"})
            return

        try:
            with app.app_context():
                session = db.get_session()
                chat_repo = ChatRepository(session)
                chat_service = ChatService(chat_repo)
                message = chat_service.send_message(game_id, user["user_id"], content)
                message_data = chat_service.message_to_dict(message)

                session.commit()

                # Broadcast to all users in the game room
                emit("chat_message", message_data, room=f"game_{game_id}")
                logger.info(f"[SocketIO] Chat from {user['username']} in game {game_id}")

        except ValueError as e:
            emit("error", {"code": "VALIDATION_ERROR", "message": str(e)})
        except Exception as e:
            logger.error(f"[SocketIO] Error sending chat: {e}")
            emit("error", {"code": "CHAT_FAILED", "message": "Failed to send message"})

