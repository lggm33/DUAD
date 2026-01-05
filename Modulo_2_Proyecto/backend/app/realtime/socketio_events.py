"""
Flask-SocketIO event handlers orchestrator.

This module registers all SocketIO event handlers by delegating to
domain-specific modules for better code organization.
"""

import logging
from flask import request
from flask_socketio import emit

from app.extensions import db
from app.domain.chat.chat_repository import ChatRepository
from app.domain.chat.chat_service import ChatService

from app.realtime.connection_events import register_connection_events
from app.realtime.game_room_events import register_game_room_events
from app.realtime.chat_events import register_chat_events
from app.realtime.combat_events import register_combat_events
from app.realtime.character_events import register_character_events

logger = logging.getLogger(__name__)

# Shared state for authenticated users by session id
authenticated_users: dict[str, dict] = {}


def register_socketio_events(socketio, app):
    """Register all SocketIO event handlers."""

    # Shared state that all modules need access to
    shared_state = {
        "authenticated_users": authenticated_users,
    }

    def broadcast_system_message(game_id: int, content: str):
        """Create and broadcast a system message to a game room."""
        session = db.get_session()
        chat_repo = ChatRepository(session)
        chat_service = ChatService(chat_repo)
        message = chat_service.send_system_message(game_id, content)
        message_data = chat_service.message_to_dict(message)
        session.commit()
        emit("chat_message", message_data, room=f"game_{game_id}")
        return message_data

    def get_user_or_error():
        """Get authenticated user or emit error."""
        user = authenticated_users.get(request.sid)
        if not user:
            emit("error", {"code": "NOT_AUTHENTICATED", "message": "Not authenticated"})
            return None
        return user

    # Helper functions shared across modules
    helpers = {
        "broadcast_system_message": broadcast_system_message,
        "get_user_or_error": get_user_or_error,
    }

    # Register all event handlers from domain-specific modules
    register_connection_events(socketio, app, shared_state, helpers)
    register_game_room_events(socketio, app, shared_state, helpers)
    register_chat_events(socketio, app, shared_state, helpers)
    register_combat_events(socketio, app, shared_state, helpers)
    register_character_events(socketio, app, shared_state, helpers)

    logger.info("[SocketIO] All event handlers registered")
