"""
Connection event handlers for SocketIO.

Handles WebSocket connection and disconnection with JWT authentication.
"""

import logging
from flask import request
from flask_socketio import emit

from app.config import get_settings
from app.extensions import db
from app.utils.jwt_service import JwtService
from app.domain.users.user_repository import UserRepository

logger = logging.getLogger(__name__)


def register_connection_events(socketio, app, shared_state, helpers):
    """Register connection-related SocketIO events."""

    authenticated_users = shared_state["authenticated_users"]
    broadcast_system_message = helpers["broadcast_system_message"]

    @socketio.on("connect")
    def handle_connect(auth):
        """Handle new WebSocket connection with JWT authentication."""
        logger.info(f"[SocketIO] New connection attempt: {request.sid}")

        if not auth or "token" not in auth:
            logger.warning("[SocketIO] Connection rejected: no token provided")
            return False

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
                    return False

                authenticated_users[request.sid] = {
                    "user_id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "game_id": None,
                    "active_encounter_id": None,
                    "character_id": None,
                }

                logger.info(f"[SocketIO] User {user.username} connected")
                emit("auth_ok", {"user_id": user.id, "username": user.username, "name": user.name})

        except Exception as e:
            logger.error(f"[SocketIO] Auth failed: {e}")
            return False

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        user = authenticated_users.pop(request.sid, None)
        if user:
            logger.info(f"[SocketIO] User {user['username']} disconnected")

            if user.get("active_encounter_id") and user.get("game_id"):
                try:
                    with app.app_context():
                        emit(
                            "player_disconnected_combat",
                            {
                                "encounter_id": user["active_encounter_id"],
                                "combatant_key": f"CHARACTER_{user.get('character_id')}",
                                "player_name": user.get("name") or user.get("username"),
                            },
                            room=f"game_{user['game_id']}",
                        )
                except Exception as e:
                    logger.error(f"[SocketIO] Error handling combat disconnect: {e}")

            if user.get("game_id"):
                try:
                    with app.app_context():
                        display_name = user.get("name") or user.get("username")
                        broadcast_system_message(user["game_id"], f"{display_name} left the chat")
                except Exception as e:
                    logger.error(f"[SocketIO] Error creating disconnect message: {e}")

